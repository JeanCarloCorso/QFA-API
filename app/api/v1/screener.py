from fastapi import APIRouter, Query, Depends, HTTPException, status
from typing import Optional, List
from pydantic import BaseModel
import yfinance as yf
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db_session
from app.models.company import Company

router = APIRouter()

class ScreenerResult(BaseModel):
    ticker: str
    company_name: str
    sector: str
    subsector: str
    score_5y: float
    debt_to_ebitda: float

async def fetch_screener_data(company: Company) -> Optional[dict]:
    """Busca dados resumidos (indicadores financeiros reais) do Yahoo Finance em thread separada."""
    def _fetch():
        try:
            t = yf.Ticker(company.ticker)
            info = t.info
            
            total_debt = info.get("totalDebt", 0.0)
            ebitda = info.get("ebitda", 0.0)
            
            if ebitda and ebitda > 0:
                debt_to_ebitda = total_debt / ebitda
            else:
                debt_to_ebitda = float('inf') # Punição para empresas sem EBITDA positivo
                
            # Score simulado baseado em rentabilidade
            profit_margin = info.get("profitMargins", 0.0)
            revenue_growth = info.get("revenueGrowth", 0.0)
            
            base_score = 5.0
            if profit_margin > 0.1: base_score += 2.0
            elif profit_margin < 0: base_score -= 2.0
            
            if revenue_growth > 0.05: base_score += 2.0
            elif revenue_growth < 0: base_score -= 2.0
            
            if debt_to_ebitda < 3.0: base_score += 1.0
            
            score_5y = max(0.0, min(10.0, base_score))
            
            return {
                "ticker": company.ticker,
                "company_name": company.company_name,
                "sector": company.sector,        # Mantém a categorização limpa do seu BD
                "subsector": company.subsector,  # Mantém a categorização limpa do seu BD
                "score_5y": round(score_5y, 2),
                "debt_to_ebitda": round(debt_to_ebitda, 2)
            }
        except Exception as e:
            logging.warning(f"Screener: Falha ao buscar dados financeiros rápidos para {company.ticker}: {e}")
            return None
            
    return await asyncio.to_thread(_fetch)


@router.get("/screener", response_model=List[ScreenerResult], tags=["Screener"])
async def screener_assets(
    min_score_5y: float = Query(0.0, description="Pontuação mínima em 5 anos (0 a 10)"),
    max_debt_ebitda: float = Query(5.0, description="Razão máxima aceitável de Dívida/EBITDA"),
    sector: Optional[str] = Query(None, description="Filtra por setor no seu Banco de Dados (ex: 'Finance')"),
    subsector: Optional[str] = Query(None, description="Filtra por subsetor especifico"),
    limit: int = Query(5, description="Quantidade máxima de ativos do banco a analisar simultaneamente no yfinance"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Screener Dinâmico.
    1. Busca o universo de empresas cadastradas no seu Banco de Dados (MySQL).
    2. Aplica filtros transacionais indexados de Setor e Subsetor economizando banda.
    3. Busca os os indicadores financeiros em tempo real no yfinance das empresas retornadas pela Query SQL.
    """
    
    # 1. Monta a Query no Banco de Dados filtrando pelas categorias principais
    query = select(Company)
    
    if sector:
        query = query.where(Company.sector == sector)
    if subsector:
        query = query.where(Company.subsector == subsector)
        
    query = query.limit(limit)
    
    result = await db.execute(query)
    companies_db = result.scalars().all()
    
    if not companies_db:
        return []
        
    # 2. Busca os indicadores em tempo real pra cada empresa validada do banco em paralelo
    tasks = [fetch_screener_data(company) for company in companies_db]
    results = await asyncio.gather(*tasks)
    
    filtered_results = []
    
    for asset in results:
        if asset is None:
            continue
            
        # 3. Filtros quantitativos de Saúde Financeira (YFinance Scope)
        if asset["score_5y"] >= min_score_5y and asset["debt_to_ebitda"] <= max_debt_ebitda:
            filtered_results.append(asset)
                
    return filtered_results
