import asyncio
import numpy as np
import pandas as pd
from typing import Dict

def calculate_altman_z_score(
    total_assets: float,
    working_capital: float,
    retained_earnings: float,
    ebit: float,
    market_value: float,
    total_liabilities: float,
    sales: float
) -> float:
    """
    Calcula o Altman Z-Score para prever a probabilidade de falência de uma empresa.
    Esta implementação utiliza a versão original de 5 variáveis para empresas de capital aberto.
    
    Fórmula utilizada: Z = 1.2(X1) + 1.4(X2) + 3.3(X3) + 0.6(X4) + 1.0(X5)
    
    Parâmetros:
        total_assets (float): Ativo Total.
        working_capital (float): Capital Circulante.
        retained_earnings (float): Lucro Retido.
        ebit (float): Lucro antes de juros e impostos (EBIT).
        market_value (float): Valor de Mercado do Patrimônio Líquido.
        total_liabilities (float): Passivo Total.
        sales (float): Vendas/Receita Total.
        
    Retorna:
        float: O Altman Z-Score calculado (arredondado em 4 casas decimais).
    """
    if total_assets <= 0 or total_liabilities <= 0:
        raise ValueError("O Ativo Total e o Passivo Total devem ser maiores que zero.")
        
    x1 = working_capital / total_assets
    x2 = retained_earnings / total_assets
    x3 = ebit / total_assets
    x4 = market_value / total_liabilities
    x5 = sales / total_assets
    
    z_score = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5
    
    return float(np.round(z_score, 4))


def calculate_beneish_m_score(
    dsri: float,
    gmi: float,
    aqi: float,
    sgi: float,
    depi: float,
    sgai: float,
    lvgi: float,
    tata: float
) -> float:
    """
    Calcula o Beneish M-Score utilizando o modelo de 8 variáveis para identificar manipulação contábil.
    
    Fórmula utilizada: 
    M = -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI
    
    Parâmetros (como proporções em relação a períodos anteriores ou ao ativo):
        dsri (float): Days Sales in Receivables Index.
        gmi (float): Gross Margin Index.
        aqi (float): Asset Quality Index.
        sgi (float): Sales Growth Index.
        depi (float): Depreciation Index.
        sgai (float): Sales General and Administrative Expenses Index.
        lvgi (float): Leverage Index.
        tata (float): Total Accruals to Total Assets.
        
    Retorna:
        float: O Beneish M-Score (arredondado para 4 casas decimais). Valores tipicamente acima de -2.22 indicam probabilidade de manipulação.
    """
    try:
        m_score = (
            -4.84 
            + 0.920 * dsri 
            + 0.528 * gmi 
            + 0.404 * aqi 
            + 0.892 * sgi 
            + 0.115 * depi 
            - 0.172 * sgai 
            + 4.679 * tata 
            - 0.327 * lvgi
        )
        return float(np.round(m_score, 4))
    except Exception as e:
        raise ValueError(f"Erro ao calcular o Beneish M-Score: {str(e)}")


async def monte_carlo_revenue_projection(
    historical_mean_growth: float,
    historical_std_dev: float,
    initial_revenue: float = 1.0,
    years: int = 5,
    iterations: int = 1000
) -> Dict[str, float]:
    """
    Executa uma Simulação de Monte Carlo assíncrona para projetar a receita corporativa 
    ao longo de um horizonte de tempo (padrão 5 anos).
    
    A função gera cenários baseados na média e no desvio padrão históricos e retorna 
    os decis projetados relevantes.
    
    Parâmetros:
        historical_mean_growth (float): Crescimento médio histórico da receita (ex: 0.05 para 5%).
        historical_std_dev (float): Desvio padrão histórico do crescimento da receita.
        initial_revenue (float, opcional): Receita base no momento inicial. Padrão: 1.0.
        years (int, opcional): Horizonte de projeção em anos. Padrão: 5.
        iterations (int, opcional): Quantidade de cenários de simulação gerados. Padrão: 1000.
        
    Retorna:
        Dict[str, float]: Um dicionário com a receita projetada no final do período para 
                          os percentis 10%, 50% (mediana) e 90%.
    """
    if historical_std_dev < 0:
        raise ValueError("O desvio padrão não pode ser negativo.")
    if iterations <= 0 or years <= 0:
        raise ValueError("A quantidade de iterações e os anos de projeção devem ser maiores que zero.")
        
    # Yielding de volta para o event loop é recomendado em rotinas async pesadas
    # como projeções estatísticas extensas a fim de não travar o FastAPI
    await asyncio.sleep(0)
    
    try:
        # Geração de matrizes de projeções através do NumPy
        # Distribuição Normal (anos x iterações)
        random_growth_rates = np.random.normal(
            loc=historical_mean_growth, 
            scale=historical_std_dev, 
            size=(iterations, years)
        )
        
        # O crescimento a cada ano é R_t = R_{t-1} * (1 + random_g)
        growth_factors = 1 + random_growth_rates
        
        # Produto cumulativo ao longo dos anos
        cumulative_growth = np.cumprod(growth_factors, axis=1)
        
        # A última coluna da matriz cumulativa representa o fator do último ano (Ano 5)
        # Multiplica-se este fator pela receita inicial
        final_revenues = initial_revenue * cumulative_growth[:, -1]
        
        # Transformação em pandas Series para melhor legibilidade analítica e extração de percentis
        series_projections = pd.Series(final_revenues)
        
        return {
            "10th_percentile": float(np.round(series_projections.quantile(0.10), 4)),
            "50th_percentile": float(np.round(series_projections.quantile(0.50), 4)),
            "90th_percentile": float(np.round(series_projections.quantile(0.90), 4))
        }
    except Exception as e:
        raise RuntimeError(f"Falha na simulação de Monte Carlo: {str(e)}")
