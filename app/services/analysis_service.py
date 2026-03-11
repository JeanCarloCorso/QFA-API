import logging
from typing import Dict, Any, Optional
from app.services.data_provider import fetch_financial_data
from app.core.math_engine import (
    calculate_altman_z_score,
    calculate_beneish_m_score,
    monte_carlo_revenue_projection
)

async def perform_quantitative_analysis(
    ticker: str, 
    selic_esperada: float, 
    ipca_esperado: float, 
    pib_esperado: float
) -> Dict[str, Any]:
    """
    Serviço centralizado para avaliar uma empresa quantitativamente, 
    fazendo a varredura do yfinance, avaliação de fraudes/falência e projeções financeiras (Monte Carlo).
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

        # 3. Monte Carlo e Projeções
        mc_params = data["monte_carlo_params"]
        mc_results = await monte_carlo_revenue_projection(
            historical_mean_growth=mc_params["historical_mean_growth"],
            historical_std_dev=mc_params["historical_std_dev"],
            initial_revenue=mc_params["initial_revenue"],
            years=5,
            iterations=1000,
            long_term_growth=pib_esperado / 100.0,  # Crescimento converge para a estimativa macro do PIB
            mean_reversion_strength=0.4,            # Força moderada de reversão
            shock_probability=0.05,                 # 5% de chance de crise
            shock_impact=-0.25                      # Impacto de -25% em caso de crise
        )
        
        # 4. Simulação de Notas/Scores combinando base, riscos e macro
        base_score = 7.0
        if manipulation_risk: base_score -= 3.0
        if bankruptcy_risk: base_score -= 4.0
        
        s1 = max(0.0, min(10.0, base_score + pib_esperado * 0.1))
        s2 = max(0.0, min(10.0, base_score + pib_esperado * 0.15 - selic_esperada * 0.05))
        s5 = max(0.0, min(10.0, base_score + pib_esperado * 0.2 - ipca_esperado * 0.1))
        s10 = max(0.0, min(10.0, base_score))
        
        # RN01: Regra do Kill Switch (Falência)
        if z_score is not None and z_score < 1.81:
            s1 = min(s1, 3.0)
            s2 = min(s2, 3.0)
            s5 = min(s5, 3.0)
            s10 = min(s10, 3.0)
            
        return {
            "scores": {
                "ano_1": round(s1, 2),
                "ano_2": round(s2, 2),
                "ano_5": round(s5, 2),
                "ano_10": round(s10, 2)
            },
            "flags": {
                "bankruptcy_risk": bankruptcy_risk,
                "manipulation_risk": manipulation_risk
            },
            "raw_data_summary": mc_results,
            "error": None
        }

    except Exception as e:
        logging.warning(f"Erro ao analisar quantitativamente {ticker}: {e}")
        return {
            "error": str(e),
            "scores": None,
            "flags": None,
            "raw_data_summary": None
        }
