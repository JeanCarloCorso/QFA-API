import asyncio
import numpy as np
from typing import Dict, Any, Optional

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


import asyncio
import numpy as np
from typing import Dict, Any, Optional


async def monte_carlo_revenue_projection(
    historical_mean_growth: float,
    historical_std_dev: float,
    initial_revenue: float = 1.0,
    years: int = 5,
    iterations: int = 1000,
    long_term_growth: Optional[float] = None,
    mean_reversion_strength: float = 0.4,
    tam: Optional[float] = None,
    # regimes econômicos
    expansion_mean: float = 0.07,
    recession_mean: float = -0.02,
    transition_prob: float = 0.15,
    # volatilidade estocástica
    vol_mean: Optional[float] = None,
    vol_reversion: float = 0.3,
    vol_volatility: float = 0.15,
    # choques
    shock_probability: float = 0.05,
    shock_impact: float = -0.25,
    seed: Optional[int] = None,
    return_distribution: bool = False
) -> Dict[str, Any]:
    """
    Simulação Monte Carlo avançada para projeção de receita corporativa.

    O modelo inclui:

    1) Crescimento log-normal da receita
    2) Reversão à média do crescimento
    3) Regimes econômicos (Markov Switching: expansão / recessão)
    4) Volatilidade estocástica
    5) Choques macroeconômicos raros
    6) Limite de crescimento via TAM (Total Addressable Market)

    Modelo de crescimento:

        g_t = g_{t-1} 
              + k*(μ - g_{t-1})
              + regime_effect
              + shock
              + ε_t

    ε_t ~ Normal(0, σ_t)

    Receita evolui:

        log(R_t) = log(R_{t-1}) + g_t * (1 - R_{t-1}/TAM)

    O fator (1 - R/TAM) impõe crescimento logístico quando TAM é definido.

    Retorna estatísticas da distribuição da receita final simulada.
    """

    if historical_std_dev < 0:
        raise ValueError("historical_std_dev deve ser positivo")

    if initial_revenue <= 0:
        raise ValueError("initial_revenue deve ser positivo")

    if iterations <= 0 or years <= 0:
        raise ValueError("years e iterations devem ser > 0")

    if not (0 <= shock_probability <= 1):
        raise ValueError("shock_probability deve estar entre 0 e 1")

    if not (0 <= transition_prob <= 1):
        raise ValueError("transition_prob deve estar entre 0 e 1")

    await asyncio.sleep(0)

    rng = np.random.default_rng(seed)

    if long_term_growth is None:
        long_term_growth = historical_mean_growth

    if vol_mean is None:
        vol_mean = historical_std_dev

    # estado inicial
    g = np.full(iterations, historical_mean_growth)
    sigma = np.full(iterations, historical_std_dev)

    # 0 = expansão, 1 = recessão
    regime = rng.integers(0, 2, size=iterations)

    log_revenue = np.full(iterations, np.log(initial_revenue))

    for _ in range(years):

        # transição de regimes (Markov)
        switch = rng.random(iterations) < transition_prob
        regime = np.where(switch, 1 - regime, regime)

        regime_mean = np.where(regime == 0, expansion_mean, recession_mean)

        # volatilidade estocástica
        sigma = (
            sigma
            + vol_reversion * (vol_mean - sigma)
            + vol_volatility * rng.normal(size=iterations)
        )

        sigma = np.abs(sigma)

        noise = rng.normal(0, sigma)

        drift = mean_reversion_strength * (long_term_growth - g)

        shocks = (
            rng.binomial(1, shock_probability, size=iterations)
            * shock_impact
        )

        g = g + drift + regime_mean + shocks + noise

        if tam is not None:
            current_revenue = np.exp(log_revenue)
            logistic_factor = 1 - (current_revenue / tam)
            logistic_factor = np.clip(logistic_factor, 0, 1)
        else:
            logistic_factor = 1

        log_revenue = log_revenue + g * logistic_factor

    revenues = np.exp(log_revenue)

    stats = {
        "mean": float(np.round(np.mean(revenues), 4)),
        "median": float(np.round(np.median(revenues), 4)),
        "std": float(np.round(np.std(revenues, ddof=1), 4)),
        "min": float(np.round(np.min(revenues), 4)),
        "max": float(np.round(np.max(revenues), 4)),
        "10th_percentile": float(np.round(np.percentile(revenues, 10), 4)),
        "25th_percentile": float(np.round(np.percentile(revenues, 25), 4)),
        "50th_percentile": float(np.round(np.percentile(revenues, 50), 4)),
        "75th_percentile": float(np.round(np.percentile(revenues, 75), 4)),
        "90th_percentile": float(np.round(np.percentile(revenues, 90), 4)),
    }

    if return_distribution:
        stats["simulated_revenues"] = np.round(revenues, 4).tolist()

    return stats