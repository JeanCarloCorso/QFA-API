from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import logging
import math
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.mysql import insert

from app.core.database import get_db_session
from app.models.company import Company
from app.models.stock_evaluation import StockEvaluation
from app.services.analysis_service import perform_quantitative_analysis

router = APIRouter()

# --- Schemas ---
class MacroDataPayload(BaseModel):
    selic_esperada: float = Field(..., description="Taxa Selic Projetada")
    ipca_esperado: float = Field(..., description="IPCA Projetado")
    pib_esperado: float = Field(..., description="PIB Crescimento Projetado")

class ScreenerSectorResponse(BaseModel):
    warning: Optional[str] = None
    data: List[Dict[str, Any]]

# --- Utilities ---
def sanitize_for_mysql(data: Any) -> Any:
    """Recursively removes math.nan and math.inf values, bypassing strict MySQL JSON constraints."""
    if isinstance(data, dict):
        return {k: sanitize_for_mysql(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_mysql(i) for i in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    return data

# --- The Background Task ---
async def process_market_sync(db: AsyncSession, macro_data: MacroDataPayload):
    """
    Motor massivo e seguro em background que processa o mercado inteiro e
    registra no banco de dados. Ignora falhas para o loop não morrer.
    """
    logging.info("Iniciando a Sincronização em Massa do Screener Quantitativo...")
    
    # 1. Busca todos os Tickers que já constam na tabela Base de Empresas
    stmt = select(Company.ticker)
    result = await db.execute(stmt)
    tickers = result.scalars().all()
    
    if not tickers:
        logging.warning("Nenhum ticker base encontrado na tabela companies.")
        return
        
    for ticker in tickers:
        try:
            logging.info(f"Screener background puxando e otimizando: {ticker}")
            
            # Análise Pesada (IO bound por causa do yfinance e math bound pelas equações algébricas Python)
            analysis_result = await perform_quantitative_analysis(
                ticker=ticker,
                selic_esperada=macro_data.selic_esperada,
                ipca_esperado=macro_data.ipca_esperado,
                pib_esperado=macro_data.pib_esperado
            )
            
            await asyncio.sleep(0.5) # Proteção limit-rate yfinance
            
            if analysis_result.get("error"):
                logging.warning(f"Ticker {ticker} ignorado devido a dados não suportados ou quebra de pipeline: {analysis_result['error']}")
                continue
                
            global_score = analysis_result.get("global_score")
            sector = analysis_result.get("raw_data_summary", {}).get("info", {}).get("sector", "Unknown")
            
            if global_score is None:
                continue

            # Sanitização estrita contra JSON NaN Error 3140 do MySQL
            sanitized_result = sanitize_for_mysql(analysis_result)

            # 3. Upsert MySQL Elegante e Super Rápido
            insert_stmt = insert(StockEvaluation).values(
                ticker=ticker,
                sector=sector,
                global_score=global_score,
                full_analysis_json=sanitized_result,
                last_updated=date.today()
            )
            
            upsert_stmt = insert_stmt.on_duplicate_key_update(
                sector=insert_stmt.inserted.sector,
                global_score=insert_stmt.inserted.global_score,
                full_analysis_json=insert_stmt.inserted.full_analysis_json,
                last_updated=insert_stmt.inserted.last_updated
            )
            
            await db.execute(upsert_stmt)
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            logging.error(f"Erro fatal crítico ignorado no loop da ação {ticker}: {e}")
            continue
            
    logging.info("Sincronização em Massa de Screener finalizada para a data de hoje.")

# --- As Novas Rotas ---

@router.get("/ticker/{ticker}", tags=["Screener Readers"])
async def get_screener_by_ticker(ticker: str, db: AsyncSession = Depends(get_db_session)):
    """
    Busca rápida do JSON avaliado completo de um único ativo armazenado.
    """
    stmt = select(StockEvaluation.full_analysis_json).where(StockEvaluation.ticker == ticker.upper())
    result = await db.execute(stmt)
    
    json_data = result.scalar_one_or_none()
    
    if not json_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Dados não encontrados para {ticker}. Certifique-se de que a empresa existe e que a rotina de Sync rodou."
        )
        
    return json_data

@router.get("/setor/{setor}", response_model=ScreenerSectorResponse, tags=["Screener Readers"])
async def get_screener_by_sector(
    setor: str,
    limit: int = Query(10, ge=1, description="O limite de companhias que quer ver ranqueadas"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Ranking setorial ranqueando com base nos global_scores.
    """
    stmt = select(StockEvaluation).where(
        StockEvaluation.sector == setor
    ).order_by(
        StockEvaluation.global_score.desc()
    ).limit(limit)
    
    result = await db.execute(stmt)
    records = result.scalars().all()
    
    warning_flag = None
    if not records:
        warning_flag = f"Dados vazios ou não encontrados para o setor '{setor}'. Rode a rota /screener/sync."
    else:
        # Se algum dos resultados retornados não for de hoje, sobe a Warning.
        if records[0].last_updated != date.today():
            warning_flag = "Os dados retornados são de um cache antigo. Certifique-se de rodar a rota /screener/sync diariamente."

    data_payload = [rec.full_analysis_json for rec in records]
    
    return ScreenerSectorResponse(
        warning=warning_flag,
        data=data_payload
    )

@router.post("/sync", status_code=status.HTTP_202_ACCEPTED, tags=["Screener Engine"])
async def trigger_mass_screener_sync(
    payload: MacroDataPayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """
    O Gateway. Recebe perspectivas Macro, cruza dados com a tabela de companhias base,
    abre threads background puxando do yfinance e gravando UPSERTS estritos na StockEvaluations
    para disponibilizar aos endpoints Readers quase instantaneamente.
    """
    background_tasks.add_task(process_market_sync, db, payload)
    
    return {"message": "Sincronização do mercado iniciada em segundo plano."}
