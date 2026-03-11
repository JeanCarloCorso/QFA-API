from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field
import logging

from app.services.analysis_service import perform_quantitative_analysis
from app.api.v1.screener import sanitize_for_mysql

router = APIRouter()

class StressTestPayload(BaseModel):
    selic_esperada: float = Field(..., description="Taxa Selic Projetada para o Cenário")
    ipca_esperado: float = Field(..., description="IPCA Projetado para o Cenário")
    pib_esperado: float = Field(..., description="PIB Crescimento Projetado para o Cenário")

@router.post("/stress-test/{ticker}", tags=["Sandbox"])
async def run_stress_test(
    payload: StressTestPayload,
    ticker: str = Path(..., description="Ticker do ativo (ex: PETR4.SA)")
):
    """
    Simula cenários macroeconômicos extremos para uma ação específica na hora, sem cache e sem salvar.
    - Recebe dados macro customizáveis.
    - Executa todo o pipeline do Quantitative Engine.
    - Devolve o payload puramente JSON com os scores.
    RESTRIÇÃO ABSOLUTA MANTIDA: Sem injeção no Banco de Dados.
    """
    try:
        logging.info(f"[Sandbox] Iniciando Stress Test na ponta para {ticker.upper()}...")
        
        # A chamada assíncrona ao motor que varre os demonstrativos via yfinance e gera a nota
        result = await perform_quantitative_analysis(
            ticker=ticker.upper(),
            selic_esperada=payload.selic_esperada,
            ipca_esperado=payload.ipca_esperado,
            pib_esperado=payload.pib_esperado
        )
        
        # O motor joga "error" se dados estão corrompidos ou ticker for inexistente
        if result.get("error"):
            logging.warning(f"[Sandbox] Stress Test do ticker {ticker.upper()} retornou erro de negócio: {result['error']}")
            raise HTTPException(status_code=404, detail=result["error"])
            
        sanitized_result = sanitize_for_mysql(result)
        return sanitized_result
        
    except HTTPException:
        # Repassa o raise HTTP 404/400 levantado pela regra de negócio
        raise
    except Exception as e:
        logging.error(f"[Sandbox] Exceção oculta durante Stress Test do ativo {ticker.upper()}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro não mapeado ao rodar Stress Test quantitativo para o ativo {ticker.upper()}.")
