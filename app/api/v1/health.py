from fastapi import APIRouter
from pydantic import BaseModel
import asyncio
import yfinance as yf
from sqlalchemy import text
from app.core.database import engine

router = APIRouter()

class DependenciesHealth(BaseModel):
    database: str
    yfinance: str

class HealthResponse(BaseModel):
    status: str
    dependencies: DependenciesHealth

async def check_database() -> str:
    """Verificação real de conexão com o banco de dados via SQLAlchemy async."""
    try:
        # Usa o motor configurado que aponta para o container MySQL real
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "ok"
    except Exception as e:
        return f"error: {str(e)}"

async def check_yfinance() -> str:
    """Verificação real de conectividade com os servidores do Yahoo Finance."""
    try:
        def _ping_yf():
            # Busca uma métrica ultra leve (fast_info) de um ativo com alta liquidez (SPY)
            ticker = yf.Ticker("SPY")
            _ = ticker.fast_info['lastPrice']
        await asyncio.to_thread(_ping_yf)
        return "ok"
    except Exception as e:
        return f"error: {str(e)}"

@router.get("/", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Endpoint abrangente para verificar a saúde da API e de suas dependências
    críticas (Provedores Financeiros).
    """

    yf_status, db_status = await asyncio.gather(check_yfinance(), check_database())
    
    # Se qualquer dependência falhar, a API sinaliza "degraded"
    overall_status = "healthy" if yf_status == "ok" and db_status == "ok" else "degraded"
    
    return {
        "status": overall_status,
        "dependencies": {
            "database": db_status,
            "yfinance": yf_status
        }
    }
