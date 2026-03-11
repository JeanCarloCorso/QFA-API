import asyncio
import yfinance as yf
import pandas as pd

async def fetch_financial_data(ticker_symbol: str) -> dict:
    """
    Busca os dados financeiros essenciais de um ticker usando yfinance.
    Executa de forma assíncrona (usando to_thread) para não bloquear o event loop.
    """
    def _fetch():
        t = yf.Ticker(ticker_symbol)
        info = t.info
        bs = t.balance_sheet
        fin = t.financials
        
        # Função auxiliar para extração segura de dados em DataFrames
        def get_value(df, key, default=0.0):
            if isinstance(df, pd.DataFrame) and key in df.index and not df.loc[key].empty:
                val = df.loc[key].iloc[0]
                if pd.isna(val):
                    return default
                return float(val)
            return default

        # 1. Extração de dados para o Altman Z-Score
        total_assets = get_value(bs, "Total Assets", info.get("totalAssets", 1.0))
        if total_assets <= 0: total_assets = 1.0 # Prevenção de divisão por zero
        
        total_liabilities = get_value(bs, "Total Liabilities Net Minority Interest", info.get("totalDebt", 1.0))
        if total_liabilities <= 0: total_liabilities = 1.0
        
        current_assets = get_value(bs, "Current Assets", 0.0)
        current_liabilities = get_value(bs, "Current Liabilities", 0.0)
        working_capital = current_assets - current_liabilities
        
        retained_earnings = get_value(bs, "Retained Earnings", 0.0)
        ebit = get_value(fin, "EBIT", info.get("ebitda", 0.0))
        market_value = info.get("marketCap", 0.0)
        
        sales = get_value(fin, "Total Revenue", info.get("totalRevenue", 0.0))

        # 2. Dados aproximados para Beneish e outras métricas
        ebitda = info.get("ebitda", 0.0)
        gross_margin = info.get("grossMargins", 0.0)
        roe = info.get("returnOnEquity", 0.0)
        beta = info.get("beta", 1.0)
        peg_ratio = info.get("pegRatio", 0.0)
        revenue_growth = info.get("revenueGrowth", 0.0)
        earnings_growth = info.get("earningsGrowth", 0.0)
        operating_cash_flow = info.get("operatingCashflow", 0.0)
        free_cash_flow = info.get("freeCashflow", 0.0)
        
        net_income = get_value(fin, "Net Income", info.get("netIncomeToCommon", 0.0))

        # Variáveis do Beneish M-Score:
        # Extração de proporções baseadas no ano base vs ano anterior (quando disponíveis)
        try:
            if isinstance(fin, pd.DataFrame) and fin.shape[1] >= 2 and isinstance(bs, pd.DataFrame) and bs.shape[1] >= 2:
                rec_t0 = float(bs.loc["Accounts Receivable"].iloc[0]) if "Accounts Receivable" in bs.index else 0.0
                rec_t1 = float(bs.loc["Accounts Receivable"].iloc[1]) if "Accounts Receivable" in bs.index else 0.0
                rev_t0 = float(fin.loc["Total Revenue"].iloc[0]) if "Total Revenue" in fin.index else 1.0
                rev_t1 = float(fin.loc["Total Revenue"].iloc[1]) if "Total Revenue" in fin.index else 1.0
                
                dsri = (rec_t0 / rev_t0) / (rec_t1 / rev_t1) if (rec_t1 and rev_t1) else 1.0
                gmi = 1.0   # Simplificado, requer COGS
                aqi = 1.0   # Simplificado, requer Ativos não circulantes
                sgi = rev_t0 / rev_t1 if rev_t1 else 1.0
                depi = 1.0  # Simplificado
                sgai = 1.0  # Simplificado
                lvgi = 1.0  # Simplificado
                tata = 0.0  # Simplificado
            else:
                dsri = 1.0; gmi = 1.0; aqi = 1.0; sgi = 1.0; depi = 1.0; sgai = 1.0; lvgi = 1.0; tata = 0.0
        except Exception:
            dsri = 1.0; gmi = 1.0; aqi = 1.0; sgi = 1.0; depi = 1.0; sgai = 1.0; lvgi = 1.0; tata = 0.0

        return {
            "altman_params": {
                "total_assets": total_assets,
                "working_capital": working_capital,
                "retained_earnings": retained_earnings,
                "ebit": ebit,
                "market_value": market_value,
                "total_liabilities": total_liabilities,
                "sales": sales
            },
            "beneish_params": {
                "dsri": dsri,
                "gmi": gmi,
                "aqi": aqi,
                "sgi": sgi,
                "depi": depi,
                "sgai": sgai,
                "lvgi": lvgi,
                "tata": tata
            },
            "monte_carlo_params": {
                "historical_mean_growth": info.get("revenueGrowth", 0.05) or 0.05,
                "historical_std_dev": 0.15, # Estático para dados ausentes na API grátis
                "initial_revenue": get_value(fin, "Total Revenue", 1.0)
            },
            "extra_metrics": {
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "total_debt": info.get("totalDebt", 0.0),
                "ebitda": ebitda,
                "gross_margin": gross_margin,
                "net_income": net_income,
                "roe": roe,
                "beta": beta,
                "peg_ratio": peg_ratio,
                "revenue_growth": revenue_growth,
                "earnings_growth": earnings_growth,
                "operating_cash_flow": operating_cash_flow,
                "free_cash_flow": free_cash_flow
            }
        }

    # Desloca chamadas blocantes de I/O de rede (yfinance) para uma thread separada
    return await asyncio.to_thread(_fetch)
