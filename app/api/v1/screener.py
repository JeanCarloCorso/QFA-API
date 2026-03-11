from fastapi import APIRouter, Query, HTTPException, status, BackgroundTasks
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import asyncio
import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.company import Company
from app.services.data_provider import fetch_financial_data
from app.core.math_engine import (
    calculate_altman_z_score,
    calculate_beneish_m_score,
    monte_carlo_revenue_projection
)

router = APIRouter()

screener_tasks_db: Dict[str, Dict[str, Any]] = {}

class ScreenerTaskResponse(BaseModel):
    task_id: str
    message: str

class HorizonScore(BaseModel):
    ano_1: float
    ano_2: float
    ano_5: float
    ano_10: float

class RiskFlags(BaseModel):
    bankruptcy_risk: bool
    manipulation_risk: bool

class ScreenerAssetResult(BaseModel):
    ticker: str
    scores: HorizonScore
    flags: RiskFlags
    raw_data_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ScreenerResultResponse(BaseModel):
    status: str
    error: Optional[str] = None
    results: Optional[List[ScreenerAssetResult]] = None


async def run_screener_task(
    task_id: str,
    sector: Optional[str],
    subsector: Optional[str],
    limit: int,
    selic_esperada: float,
    ipca_esperado: float,
    pib_esperado: float
):
    try:
        # Precisamos instanciar uma sessão isolada para o background task
        async with AsyncSessionLocal() as db:
            query = select(Company)
            if sector:
                query = query.where(Company.sector == sector)
            if subsector:
                query = query.where(Company.subsector == subsector)
                
            result = await db.execute(query)
            companies_db = result.scalars().all()
            
        if not companies_db:
            screener_tasks_db[task_id] = {
                "status": "completed",
                "results": []
            }
            return

        # Avaliação de cada empresa individualmente com métricas parciais completas do nosso motor
        async def evaluate_company(company: Company):
            try:
                data = await fetch_financial_data(company.ticker)
                
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
                    
                # 3. Monte Carlo e Projeções
                mc_params = data["monte_carlo_params"]
                mc_results = await monte_carlo_revenue_projection(
                    historical_mean_growth=mc_params["historical_mean_growth"],
                    historical_std_dev=mc_params["historical_std_dev"],
                    initial_revenue=mc_params["initial_revenue"],
                    years=5,
                    iterations=1000
                )
                
                # 4. Cálculo de Score Completo
                base_score = 7.0
                if manipulation_risk: base_score -= 3.0
                if bankruptcy_risk: base_score -= 4.0
                
                s1 = max(0.0, min(10.0, base_score + pib_esperado * 0.1))
                s2 = max(0.0, min(10.0, base_score + pib_esperado * 0.15 - selic_esperada * 0.05))
                s5 = max(0.0, min(10.0, base_score + pib_esperado * 0.2 - ipca_esperado * 0.1))
                s10 = max(0.0, min(10.0, base_score))
                
                if z_score is not None and z_score < 1.81:
                    s1 = min(s1, 3.0)
                    s2 = min(s2, 3.0)
                    s5 = min(s5, 3.0)
                    s10 = min(s10, 3.0)
                    
                return {
                    "company": company,
                    "scores": {"ano_1": round(s1, 2), "ano_2": round(s2, 2), "ano_5": round(s5, 2), "ano_10": round(s10, 2)},
                    "flags": {"bankruptcy_risk": bankruptcy_risk, "manipulation_risk": manipulation_risk},
                    "raw_data_summary": mc_results,
                    "error": None
                }
            except Exception as e:
                logging.warning(f"Erro ao analisar quantitativamente {company.ticker}: {e}")
                return None

        # Disparamos I/O Async em lote massivo contra todas as empresas qualificadas daquele setor
        tasks = [evaluate_company(c) for c in companies_db]
        evaluations = await asyncio.gather(*tasks)
        
        valid_evaluations = [ev for ev in evaluations if ev is not None]
        
        # Ordenar das mais bem avaliadas para as piores (Descendente pelo ano_5)
        valid_evaluations.sort(key=lambda x: x["scores"]["ano_5"], reverse=True)
        
        # Ceifar do topo as melhores na quantidade solicitada pelo usuário
        top_evaluations = valid_evaluations[:limit]
        
        final_results = []
        for ev in top_evaluations:
            final_results.append({
                "ticker": ev["company"].ticker,
                "scores": ev["scores"],
                "flags": ev["flags"],
                "raw_data_summary": ev["raw_data_summary"],
                "error": ev["error"]
            })
            
        # Gravar Status de Sucesso no DB em memória
        screener_tasks_db[task_id] = {
            "status": "completed",
            "results": final_results
        }
        
    except Exception as e:
        logging.error(f"Erro no processamento background da varredura {task_id}: {e}")
        screener_tasks_db[task_id] = {
            "status": "failed",
            "error": str(e)
        }

@router.get("/screener", status_code=status.HTTP_202_ACCEPTED, response_model=ScreenerTaskResponse, tags=["Screener"])
async def start_screener(
    background_tasks: BackgroundTasks,
    sector: Optional[str] = Query(None, description="Filtra por setor no seu Banco de Dados (ex: 'Finance')"),
    subsector: Optional[str] = Query(None, description="Filtra por subsetor especifico"),
    limit: int = Query(5, description="Quantidade máxima de ativos a retornar após a análise completa"),
    selic_esperada: float = Query(10.5, ge=0.0, le=100.0, description="Taxa Selic esperada em %"),
    ipca_esperado: float = Query(4.5, ge=-20.0, le=100.0, description="IPCA esperado em %"),
    pib_esperado: float = Query(2.0, ge=-20.0, le=50.0, description="Crescimento do PIB esperado em %")
):
    """
    Inicia o Screener Quantitativo de forma assíncrona para evitar Timeouts HTTP.
    Filtra por setor, executa os testes de estresse para cada empresa do banco, 
    ordena da melhor para a pior e retorna o task_id.
    """
    
    task_id = str(uuid.uuid4())
    screener_tasks_db[task_id] = {"status": "processing"}
    
    background_tasks.add_task(
        run_screener_task,
        task_id=task_id,
        sector=sector,
        subsector=subsector,
        limit=limit,
        selic_esperada=selic_esperada,
        ipca_esperado=ipca_esperado,
        pib_esperado=pib_esperado
    )
    
    return ScreenerTaskResponse(
        task_id=task_id,
        message=f"A varredura do screener foi enfileirada com sucesso."
    )

@router.get("/screener/result/{task_id}", response_model=ScreenerResultResponse, tags=["Screener"])
async def get_screener_result(task_id: str):
    """
    Faz um 'polling' para resgatar os resultados consolidados do screener quantitativo
    com base no task_id. Responde em semelhança ao /analysis/result.
    """
    task_data = screener_tasks_db.get(task_id)
    
    if not task_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task ID não encontrado ou expirou."
        )
        
    return ScreenerResultResponse(**task_data)
