import logging
import numpy as np
from typing import Dict, Any, Optional

from app.services.data_provider import fetch_financial_data
from app.core.math_engine import (
    calculate_solvency_metrics,
    calculate_profitability_metrics,
    calculate_efficiency_metrics,
    calculate_valuation_metrics,
    calculate_altman_z_score,
    calculate_beneish_m_score,
    monte_carlo_revenue_projection
)
from app.services.scoring_engine import calculate_horizon_scores

async def generate_full_analysis(ticker_data: Dict[str, Any], macro_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Função principal de orquestração que processa todas as métricas fundamentalistas e
    quantitativas a partir de dados brutos da empresa e do cenário macroeconômico.
    Retorna um dicionário gigante com todas as categorias: solvency, profitability, 
    efficiency, valuation, forensic_scores e projections.
    Possui tratamento de erros com fallback para garantir que a quebra de um indicador 
    não derrube a análise completa.
    """
    
    # 1. Extração Segura de Macroeconômicos
    selic_esperada = macro_data.get("selic_esperada", 10.5)
    ipca_esperado = macro_data.get("ipca_esperado", 4.5)
    pib_esperado = macro_data.get("pib_esperado", 2.0)
    
    # 2. Extração Segura de Dados Financeiros (Prevenindo KeyError)
    sector = ticker_data.get("sector", "Unknown")
    industry = ticker_data.get("industry", "Unknown")
    
    is_utility = (
        "utilities" in sector.lower() or 
        "water" in industry.lower() or 
        "power" in industry.lower() or
        "energy" in sector.lower()
    )
    total_assets = ticker_data.get("total_assets", 0.0)
    current_assets = ticker_data.get("current_assets", 0.0)
    working_capital = ticker_data.get("working_capital", 0.0)
    retained_earnings = ticker_data.get("retained_earnings", 0.0)
    ebit = ticker_data.get("ebit", 0.0)
    ebitda = ticker_data.get("ebitda", 0.0)
    net_income = ticker_data.get("net_income", 0.0)
    revenue = ticker_data.get("revenue", 0.0)
    gross_profit = ticker_data.get("gross_profit", 0.0)
    
    peg_ratio = ticker_data.get("peg_ratio", 0.0)
    beta = ticker_data.get("beta", 1.0)
    revenue_growth = ticker_data.get("revenue_growth", 0.0)
    earnings_growth = ticker_data.get("earnings_growth", 0.0)
    operating_cash_flow = ticker_data.get("operating_cash_flow", 0.0)
    free_cash_flow = ticker_data.get("free_cash_flow", 0.0)
    
    market_cap = ticker_data.get("market_cap", 0.0)
    total_liabilities = ticker_data.get("total_liabilities", 0.0)
    current_liabilities = ticker_data.get("current_liabilities", 0.0)
    total_debt = ticker_data.get("total_debt", 0.0)
    total_equity = ticker_data.get("total_equity", 0.0)
    cash_and_equivalents = ticker_data.get("cash_and_equivalents", 0.0)
    
    tax_rate = ticker_data.get("tax_rate", 0.34) # Padrão tributário corporativo comum
    
    # 2.1 Extração para Motores Específicos (Beneish)
    dsri = ticker_data.get("dsri", 1.0)
    gmi = ticker_data.get("gmi", 1.0)
    aqi = ticker_data.get("aqi", 1.0)
    sgi = ticker_data.get("sgi", 1.0)
    depi = ticker_data.get("depi", 1.0)
    sgai = ticker_data.get("sgai", 1.0)
    lvgi = ticker_data.get("lvgi", 1.0)
    tata = ticker_data.get("tata", 0.0)
    
    # 2.2 Extração para Motores de Projeção (Monte Carlo)
    historical_mean_growth = ticker_data.get("historical_mean_growth", 0.05)
    historical_std_dev = ticker_data.get("historical_std_dev", 0.15)
    initial_revenue = ticker_data.get("initial_revenue", 1.0)
    if initial_revenue <= 0:
        initial_revenue = 1.0

    # 3. Orquestração de Cálculo com Fallbacks Individuais
    
    # --- Solvency (Solvência e Liquidez) ---
    solvency = {}
    try:
        solvency = calculate_solvency_metrics(
            total_debt=total_debt,
            cash_and_equivalents=cash_and_equivalents,
            ebitda=ebitda,
            current_assets=current_assets,
            current_liabilities=current_liabilities
        )
    except Exception as e:
        logging.warning(f"Erro ao calcular métricas de Solvência: {e}")
        solvency = {"error": str(e)}

    # --- Profitability (Rentabilidade - ROE / ROIC) ---
    profitability = {}
    
    # Passo 2: Sanity Check de Lucro (Net Income)
    profitability_warning = None
    if not net_income or net_income == 0:
        profitability_warning = "Lucro Líquido nulo ou zero. ROE e Margens podem estar distorcidos."
        
    try:
        profitability = calculate_profitability_metrics(
            net_income=net_income,
            total_equity=total_equity,
            ebit=ebit,
            tax_rate=tax_rate,
            total_debt=total_debt,
            cash_and_equivalents=cash_and_equivalents
        )
        if profitability_warning:
            profitability["data_warning"] = profitability_warning
    except Exception as e:
        logging.warning(f"Erro ao calcular métricas de Rentabilidade: {e}")
        profitability = {"error": str(e)}

    # Passo 3: Roteamento Setorial (A Correção do EV/EBITDA)
    is_financial_or_holding = (
        sector in ["Financial Services", "Financial"] or
        industry in ["Conglomerates", "Banks - Regional", "Banks - Diversified"]
    )
    
    # --- Efficiency (Eficiência: Margens) ---
    efficiency = {}
    if is_financial_or_holding:
        efficiency = {"warning": "Métricas de margem clássicas (Bruta/EBITDA) não se aplicam a Bancos/Holdings."}
    else:
        try:
            efficiency = calculate_efficiency_metrics(
                gross_profit=gross_profit,
                ebitda=ebitda,
                net_income=net_income,
                revenue=revenue
            )
        except Exception as e:
            logging.warning(f"Erro ao calcular métricas de Eficiência: {e}")
            efficiency = {"error": str(e)}

    # --- Valuation (Múltiplos - P/L, EV/EBITDA) ---
    valuation = {}
    if is_financial_or_holding:
        try:
            p_vp = float(np.round(market_cap / total_equity, 4)) if total_equity > 0 else float('inf')
            valuation = {
                "price_to_book": p_vp, 
                "warning": "Valuation ajustado para modelo bancário (P/VP)."
            }
        except Exception as e:
            valuation = {"error": f"Erro ao calcular P/VP bancário: {e}"}
    else:
        try:
            valuation = calculate_valuation_metrics(
                market_cap=market_cap,
                net_income=net_income,
                total_debt=total_debt,
                cash_and_equivalents=cash_and_equivalents,
                ebitda=ebitda
            )
            valuation["peg_ratio"] = peg_ratio
        except Exception as e:
            logging.warning(f"Erro ao calcular Valuation: {e}")
            valuation = {"error": str(e)}

    # --- Information, Risk, Growth e Cash Flow ---
    info = {
        "sector": sector,
        "industry": industry
    }
    
    risk = {
        "beta": beta
    }
    
    growth = {
        "revenue_growth": revenue_growth,
        "earnings_growth": earnings_growth
    }
    
    ocf_ni = operating_cash_flow / net_income if net_income > 0 else 1.0
    fcf_m = free_cash_flow / revenue if revenue > 0 else 0.0
    
    cash_flow = {
        "operating_cash_flow_to_net_income": ocf_ni,
        "free_cash_flow_margin": fcf_m
    }

    # --- Forensic Scores (Risco de Falência e Manipulação) ---
    forensic_scores = {}
    try:
        z_score = calculate_altman_z_score(
            total_assets=total_assets,
            working_capital=working_capital,
            retained_earnings=retained_earnings,
            ebit=ebit,
            market_value=market_cap,
            total_liabilities=total_liabilities,
            sales=revenue
        )
        forensic_scores["altman_z_score"] = z_score
        
        if is_utility:
            forensic_scores["bankruptcy_risk"] = False
            forensic_scores["z_score_warning"] = "Altman Z-Score ignorado (Setor de Utilidade Pública / Capital Intensivo)."
        else:
            forensic_scores["bankruptcy_risk"] = z_score < 1.81
    except Exception as e:
        logging.warning(f"Erro no Altman Z-Score: {e}")
        forensic_scores["altman_error"] = str(e)
        forensic_scores["bankruptcy_risk"] = False

    try:
        m_score = calculate_beneish_m_score(
            dsri=dsri, gmi=gmi, aqi=aqi, sgi=sgi, 
            depi=depi, sgai=sgai, lvgi=lvgi, tata=tata
        )
        forensic_scores["beneish_m_score"] = m_score
        forensic_scores["manipulation_risk"] = m_score > -2.22
    except Exception as e:
        logging.warning(f"Erro no Beneish M-Score: {e}")
        forensic_scores["beneish_error"] = str(e)
        forensic_scores["manipulation_risk"] = False

    # --- Projections (Simulação Estocástica Monte Carlo de Receitas) ---
    projections = {}
    try:
        projections = await monte_carlo_revenue_projection(
            historical_mean_growth=historical_mean_growth,
            historical_std_dev=historical_std_dev,
            initial_revenue=initial_revenue,
            years=5,
            iterations=1000,
            long_term_growth=pib_esperado / 100.0,
            mean_reversion_strength=0.4,
            shock_probability=0.05,
            shock_impact=-0.25
        )
    except Exception as e:
        logging.warning(f"Erro no Monte Carlo: {e}")
        projections = {"error": str(e)}

    # Retorno Centralizado e Limpo
    return {
        "info": info,
        "risk": risk,
        "solvency": solvency,
        "profitability": profitability,
        "efficiency": efficiency,
        "growth": growth,
        "cash_flow": cash_flow,
        "valuation": valuation,
        "forensic_scores": forensic_scores,
        "projections": projections
    }

async def perform_quantitative_analysis(
    ticker: str, 
    selic_esperada: float, 
    ipca_esperado: float, 
    pib_esperado: float
) -> Dict[str, Any]:
    """
    Função Wrapper Legacy - Mantida para garantir compatibilidade retroativa com as 
    Rotas (API Endpoints) que esperam o resultado sumarizado focado nos Horizon Scores.
    Busca os dados do yfinance, formata para formato flat e direciona ao motor completo.
    """
    try:
        data = await fetch_financial_data(ticker)
        alt = data.get("altman_params", {})
        ben = data.get("beneish_params", {})
        mc = data.get("monte_carlo_params", {})
        ext = data.get("extra_metrics", {})
        
        # Constrói o Dicionário Flat Universal
        ticker_data = {
            "sector": ext.get("sector", "Unknown"),
            "industry": ext.get("industry", "Unknown"),
            "total_assets": alt.get("total_assets", 0.0),
            "working_capital": alt.get("working_capital", 0.0),
            "retained_earnings": alt.get("retained_earnings", 0.0),
            "ebit": alt.get("ebit", 0.0),
            "market_cap": alt.get("market_value", 0.0),
            "total_liabilities": alt.get("total_liabilities", 0.0),
            "revenue": alt.get("sales", 0.0),
            
            "dsri": ben.get("dsri", 1.0),
            "gmi": ben.get("gmi", 1.0),
            "aqi": ben.get("aqi", 1.0),
            "sgi": ben.get("sgi", 1.0),
            "depi": ben.get("depi", 1.0),
            "sgai": ben.get("sgai", 1.0),
            "lvgi": ben.get("lvgi", 1.0),
            "tata": ben.get("tata", 0.0),
            
            "historical_mean_growth": mc.get("historical_mean_growth", 0.05),
            "historical_std_dev": mc.get("historical_std_dev", 0.15),
            "initial_revenue": mc.get("initial_revenue", 1.0),
            
            "total_debt": ext.get("total_debt", 0.0),
            "ebitda": ext.get("ebitda", 0.0),
            "gross_profit": ext.get("gross_margin", 0.0) * alt.get("sales", 1.0),
            "net_income": ext.get("net_income", 0.0),
            "total_equity": alt.get("total_assets", 0.0) - alt.get("total_liabilities", 0.0),
            "current_assets": alt.get("total_assets", 0.0),  # fallback temporário
            "current_liabilities": alt.get("total_liabilities", 0.0), # fallback temporário
            "cash_and_equivalents": 0.0,
            "tax_rate": 0.34,
            
            "beta": ext.get("beta", 1.0),
            "peg_ratio": ext.get("peg_ratio", 0.0),
            "revenue_growth": ext.get("revenue_growth", 0.0),
            "earnings_growth": ext.get("earnings_growth", 0.0),
            "operating_cash_flow": ext.get("operating_cash_flow", 0.0),
            "free_cash_flow": ext.get("free_cash_flow", 0.0)
        }
        
        macro_data = {
            "selic_esperada": selic_esperada,
            "ipca_esperado": ipca_esperado,
            "pib_esperado": pib_esperado
        }
        
        # Chama a orquestração central completa
        full_analysis = await generate_full_analysis(ticker_data, macro_data)
        
        # Recupera as flags requeridas nos endpoints
        manipulation_risk = full_analysis.get("forensic_scores", {}).get("manipulation_risk", False)
        bankruptcy_risk = full_analysis.get("forensic_scores", {}).get("bankruptcy_risk", False)
        z_score = full_analysis.get("forensic_scores", {}).get("altman_z_score")
        # Calcula as notas baseadas na lógica quantitativa
        calculated_scores = calculate_horizon_scores(
            full_analysis=full_analysis,
            macro_data=macro_data
        )
            
        return {
            "global_score": calculated_scores.get("global_score"),
            "scores": {
                "ano_1": calculated_scores.get("ano_1"),
                "ano_2": calculated_scores.get("ano_2"),
                "ano_5": calculated_scores.get("ano_5"),
                "ano_10": calculated_scores.get("ano_10")
            },
            "flags": {
                "bankruptcy_risk": bankruptcy_risk,
                "manipulation_risk": manipulation_risk
            },
            "raw_data_summary": full_analysis,
            "error": None,
            "status": "completed",
            "ticker": ticker
        }

    except Exception as e:
        logging.warning(f"Erro ao analisar quantitativamente {ticker}: {e}")
        return {
            "error": str(e),
            "scores": None,
            "flags": None,
            "raw_data_summary": None
        }
