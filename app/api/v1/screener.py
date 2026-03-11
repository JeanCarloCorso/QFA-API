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
from app.schemas.analysis import AnalysisResultBase
from app.services.analysis_service import perform_quantitative_analysis

router = APIRouter()

screener_tasks_db: Dict[str, Dict[str, Any]] = {}

class ScreenerTaskResponse(BaseModel):
    task_id: str
    message: str

class ScreenerAssetResult(AnalysisResultBase):
    ticker: str

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
                result = await perform_quantitative_analysis(
                    ticker=company.ticker,
                    selic_esperada=selic_esperada,
                    ipca_esperado=ipca_esperado,
                    pib_esperado=pib_esperado
                )
                
                if result.get("error"):
                    return None
                    
                return {
                    "company": company,
                    "global_score": result.get("global_score"),
                    "scores": result["scores"],
                    "flags": result["flags"],
                    "raw_data_summary": result["raw_data_summary"],
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
                "global_score": ev.get("global_score"),
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
