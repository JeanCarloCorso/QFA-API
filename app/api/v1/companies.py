from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.mysql import insert

from app.core.database import get_db_session
from app.models.company import Company
import logging

router = APIRouter()

# --- Pydantic Schemas de Request/Response ---


class SyncResponse(BaseModel):
    total_received_from_api: int
    total_processed: int
    message: str

@router.get("/sync", response_model=SyncResponse, tags=["Companies"])
async def sync_companies(db: AsyncSession = Depends(get_db_session)):
    """
    Endpoint de sincronização em massa de Ativos via GET.
    Busca a listagem oficial de todos os papéis da B3 pelo provedor brapi.dev e faz o UPSERT
    assíncrono em altíssima velocidade direto no banco de dados da QFA-API.
    """
    url = "https://brapi.dev/api/quote/list"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        logging.error(f"Falha ao buscar dados da BRAPI: {e}")
        raise HTTPException(status_code=502, detail="Erro de comunicação com o provedor de dados financeiros brapi.dev")
        
    stocks = data.get("stocks", [])
    if not stocks:
        raise HTTPException(status_code=404, detail="Nenhuma ação retornada pela API.")

    processed = 0
    
    # Processamento em lote para UPSERT
    for stock_info in stocks:
        symbol = stock_info.get("stock", "").upper()
        if not symbol:
            continue
            
        ticker_sa = f"{symbol}.SA"
        company_name = stock_info.get("name") or symbol
        sector = stock_info.get("sector") or "Desconhecido"
        # BRAPI list não fornece uma indústria granular sempre, mapeamos sector como subsector se faltar
        subsector = sector 

        try:
            stmt = insert(Company).values(
                ticker=ticker_sa,
                company_name=company_name,
                sector=sector,
                subsector=subsector
            )
            
            upsert_stmt = stmt.on_duplicate_key_update(
                company_name=stmt.inserted.company_name,
                sector=stmt.inserted.sector,
                subsector=stmt.inserted.subsector
            )
            
            await db.execute(upsert_stmt)
            processed += 1
            
        except Exception as e:
            await db.rollback()
            logging.warning(f"Erro ao inserir {ticker_sa}: {e}")
            continue
            
    # Commita a transação inteira no final do lote para altíssima densidade de gravação
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logging.error(f"Erro no commit em lote: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao gravar no banco de dados.")

    return SyncResponse(
        total_received_from_api=len(stocks),
        total_processed=processed,
        message="Sincronização concluída com sucesso."
    )
