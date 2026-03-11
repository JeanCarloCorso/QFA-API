from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field
import logging
import uuid
from typing import Dict, Any, Optional

from app.services.data_provider import fetch_financial_data
from app.core.math_engine import (
    calculate_altman_z_score,
    calculate_beneish_m_score,
    monte_carlo_revenue_projection
)

router = APIRouter()

# Dicionário em memória para armazenar os resultados das tarefas (simulando um Redis/DB)
tasks_db: Dict[str, Dict[str, Any]] = {}

# --- Pydantic Models ---

class MacroProjections(BaseModel):
    selic_esperada: float = Field(..., ge=0.0, le=100.0, description="Taxa Selic esperada em %")
    ipca_esperado: float = Field(..., ge=-20.0, le=100.0, description="IPCA esperado em %")
    pib_esperado: float = Field(..., ge=-20.0, le=50.0, description="Crescimento do PIB esperado em %")

class TaskResponse(BaseModel):
    task_id: str
    message: str

class HorizonScore(BaseModel):
    ano_1: float = Field(..., ge=0, le=10)
    ano_2: float = Field(..., ge=0, le=10)
    ano_5: float = Field(..., ge=0, le=10)
    ano_10: float = Field(..., ge=0, le=10)

class RiskFlags(BaseModel):
    bankruptcy_risk: bool
    manipulation_risk: bool

class AnalysisResult(BaseModel):
    status: str
    ticker: Optional[str] = None
    scores: Optional[HorizonScore] = None
    flags: Optional[RiskFlags] = None
    raw_data_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# --- Background Processing Function ---

async def process_quant_analysis(task_id: str, ticker: str, payload: MacroProjections):
    """
    Função executada em background para processar os dados financeiros e rodar os modelos.
    """
    try:
        data = await fetch_financial_data(ticker)
        
        # 1. Altman Z-Score
        altman_params = data["altman_params"]
        try:
            z_score = calculate_altman_z_score(**altman_params)
            bankruptcy_risk = z_score < 1.81 if z_score is not None else False
        except Exception:
            z_score = None
            bankruptcy_risk = False

        # 2. Beneish M-Score
        beneish_params = data["beneish_params"]
        try:
            m_score = calculate_beneish_m_score(**beneish_params)
            manipulation_risk = m_score > -2.22 if m_score is not None else False
        except Exception:
            manipulation_risk = False

        # 3. Monte Carlo e Projeções (Simulação de Scores baseado em macro + MC)
        mc_params = data["monte_carlo_params"]
        # Executa MC em background, não afeta o response de 202
        mc_results = await monte_carlo_revenue_projection(
            historical_mean_growth=mc_params["historical_mean_growth"],
            historical_std_dev=mc_params["historical_std_dev"],
            initial_revenue=mc_params["initial_revenue"],
            years=5,
            iterations=1000
        )
        
        # Simulação estruturada das notas considerando o macro
        # Em um cenário real, isso envolveria os outputs de Monte Carlo combinados
        base_score = 7.0
        if manipulation_risk: base_score -= 3.0
        if bankruptcy_risk: base_score -= 4.0
        
        s1 = max(0.0, min(10.0, base_score + payload.pib_esperado * 0.1))
        s2 = max(0.0, min(10.0, base_score + payload.pib_esperado * 0.15 - payload.selic_esperada * 0.05))
        s5 = max(0.0, min(10.0, base_score + payload.pib_esperado * 0.2 - payload.ipca_esperado * 0.1))
        s10 = max(0.0, min(10.0, base_score))
        
        # RN01: Regra do Kill Switch (Falência)
        if z_score is not None and z_score < 1.81:
            s1 = min(s1, 3.0)
            s2 = min(s2, 3.0)
            s5 = min(s5, 3.0)
            s10 = min(s10, 3.0)
            
        scores = HorizonScore(
            ano_1=s1,
            ano_2=s2,
            ano_5=s5,
            ano_10=s10
        )
        
        flags = RiskFlags(
            bankruptcy_risk=bankruptcy_risk,
            manipulation_risk=manipulation_risk
        )

        # Atualiza o DB em memória com o sucesso
        tasks_db[task_id] = {
            "status": "completed",
            "ticker": ticker.upper(),
            "scores": scores.model_dump(),
            "flags": flags.model_dump(),
            "raw_data_summary": mc_results
        }

    except Exception as e:
        logging.error(f"Erro no processamento da task {task_id} para {ticker}: {e}")
        # Atualiza o DB em memória com o erro
        tasks_db[task_id] = {
            "status": "failed",
            "error": str(e)
        }


# --- Endpoints ---

@router.post("/quant/{ticker}", status_code=status.HTTP_202_ACCEPTED, response_model=TaskResponse, tags=["Analysis"])
async def start_quant_analysis(ticker: str, payload: MacroProjections, background_tasks: BackgroundTasks):
    """
    Inicia o processamento quantitativo em background para evitar timeouts.
    Retorna imediatamente um task_id para acompanhamento.
    """
    task_id = str(uuid.uuid4())
    
    # Registra o estado inicial da task
    tasks_db[task_id] = {"status": "processing"}
    
    # Adiciona o trabalho pesado ao background
    background_tasks.add_task(process_quant_analysis, task_id, ticker, payload)
    
    return TaskResponse(
        task_id=task_id,
        message=f"A análise para {ticker.upper()} foi enfileirada com sucesso."
    )


@router.get("/result/{task_id}", response_model=AnalysisResult, tags=["Analysis"])
async def get_analysis_result(task_id: str):
    """
    Restaura os resultados consolidados do processamento quantitativo
    com base no task_id fornecido em /quant/{ticker}.
    """
    task_data = tasks_db.get(task_id)
    
    if not task_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task ID não encontrado ou expirou."
        )
        
    return AnalysisResult(**task_data)
