from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

from app.services.data_provider import fetch_financial_data
from app.core.math_engine import (
    calculate_altman_z_score,
    calculate_beneish_m_score,
    monte_carlo_revenue_projection
)

app = FastAPI(
    title="QFA-API",
    description="Quantitative Financial Analysis API",
    version="0.1.0"
)

# Definindo o modelo de Input (Payload JSON esperado)
class MacroProjections(BaseModel):
    selic_esperada: float
    ipca_esperado: float

@app.post("/api/v1/analysis/quant/{ticker}")
async def analyze_quant(ticker: str, payload: MacroProjections):
    """
    Endpoint para analisar indicadores quantitativos de uma ação na bolsa
    utilizando web scraping de dados reais via yfinance e projeções estatísticas.
    """
    try:
        data = await fetch_financial_data(ticker)
        
        # 1. Altman Z-Score Application
        altman_params = data["altman_params"]
        try:
            z_score = calculate_altman_z_score(**altman_params)
            # Thresholds típicos para empresas não-manufatureiras
            if z_score > 2.6:
                z_alert = "Zona Segura"
            elif 1.1 <= z_score <= 2.6:
                z_alert = "Zona Cinzenta (Atenção)"
            else:
                z_alert = "Zona de Risco de Falência"
        except Exception as e:
            z_score = None
            z_alert = f"Erro no cálculo: {str(e)}"

        # 2. Beneish M-Score Application
        beneish_params = data["beneish_params"]
        try:
            m_score = calculate_beneish_m_score(**beneish_params)
            m_alert = "Possível Manipulação (-2.22 excedido)" if m_score > -2.22 else "Manipulação Improvável"
        except Exception as e:
            m_score = None
            m_alert = f"Erro no cálculo: {str(e)}"

        # 3. Monte Carlo Application
        mc_params = data["monte_carlo_params"]
        mc_results = await monte_carlo_revenue_projection(
            historical_mean_growth=mc_params["historical_mean_growth"],
            historical_std_dev=mc_params["historical_std_dev"],
            initial_revenue=mc_params["initial_revenue"],
            years=5,
            iterations=1000
        )

        return {
            "ticker": ticker.upper(),
            "macro_context": {
                "selic_esperada": payload.selic_esperada,
                "ipca_esperado": payload.ipca_esperado
            },
            "financial_metrics": data["extra_metrics"],
            "quantitative_analysis": {
                "altman_z_score": {
                    "score": z_score,
                    "alert": z_alert
                },
                "beneish_m_score": {
                    "score": m_score,
                    "alert": m_alert
                },
                "monte_carlo_projection_5y": mc_results
            }
        }

    except Exception as e:
        logging.error(f"Erro ao analisar o ticker {ticker}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro interno ao processar a análise financeira do ativo: {str(e)}"
        )
