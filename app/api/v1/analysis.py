from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field
import logging
import uuid
from typing import Dict, Any, Optional

from app.schemas.analysis import MacroProjections, AnalysisResultBase
from app.services.analysis_service import perform_quantitative_analysis

router = APIRouter()

# Dicionário em memória para armazenar os resultados das tarefas (simulando um Redis/DB)
tasks_db: Dict[str, Dict[str, Any]] = {}

# --- Pydantic Models ---

class TaskResponse(BaseModel):
    task_id: str
    message: str

class AnalysisResult(AnalysisResultBase):
    status: str
    ticker: Optional[str] = None


# --- Background Processing Function ---

async def process_quant_analysis(task_id: str, ticker: str, payload: MacroProjections):
    """
    Função executada em background para processar os dados financeiros e rodar os modelos.
    """
    try:
        result = await perform_quantitative_analysis(
            ticker=ticker,
            selic_esperada=payload.selic_esperada,
            ipca_esperado=payload.ipca_esperado,
            pib_esperado=payload.pib_esperado
        )
        
        if result.get("error"):
            tasks_db[task_id] = {
                "status": "failed",
                "error": result["error"]
            }
        else:
            # result is already completely formatted by perform_quantitative_analysis
            tasks_db[task_id] = result
            
            
    except Exception as e:
        logging.error(f"Erro no processamento da task {task_id} para {ticker}: {e}")
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
