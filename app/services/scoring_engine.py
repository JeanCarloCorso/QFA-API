import logging
import numpy as np
from typing import Dict, Any

def _safe_float(val: Any, default: float = 0.0) -> float:
    """
    Converte número para float com total segurança.
    Trata inputs None, strings corrompidas, literais infinitos e NaNs estatísticos.
    """
    try:
        if val is None:
            return default
        f_val = float(val)
        if np.isnan(f_val) or np.isinf(f_val):
            return default
        return f_val
    except (TypeError, ValueError):
        return default

def calculate_horizon_scores(full_analysis: Dict[str, Any], macro_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Motor central de Scoring Quantitativo e Fundamentalista da API QFA.
    Avalia risco, métricas de crescimento, qualidade estrutural (Balanço e DRE)
    e fluxo de caixa para horizontes de curto a longo prazo.
    """
    
    # --- 1. Extração Macro e Construção de Proxies ---
    selic_esperada = _safe_float(macro_data.get("selic_esperada", 10.5))
    ipca_esperado = _safe_float(macro_data.get("ipca_esperado", 4.5))
    pib_esperado = _safe_float(macro_data.get("pib_esperado", 2.0))
    
    selic_decimal = selic_esperada / 100.0
    equity_risk_premium = 0.04  # Prêmio de Risco exigido de ações (ERP padrão de 4%)
    wacc_proxy = selic_decimal + equity_risk_premium
    
    # --- 2. Extração Segura de Submódulos Analíticos ---
    solvency = full_analysis.get("solvency", {}) or {}
    profitability = full_analysis.get("profitability", {}) or {}
    efficiency = full_analysis.get("efficiency", {}) or {}
    valuation = full_analysis.get("valuation", {}) or {}
    forensics = full_analysis.get("forensic_scores", {}) or {}
    
    # Novos Submódulos Analíticos Projetados (Resiliente contra dicts que não possuem a chave)
    # Recomenda-se adicionar essas extrações em `analysis_service.py` na próxima versão.
    growth = full_analysis.get("growth", {}) or {} 
    cash_flow = full_analysis.get("cash_flow", {}) or {}
    risk = full_analysis.get("risk", {}) or {}
    info = full_analysis.get("info", {}) or {}

    # --- 3. Extração das Métricas ---
    # Rentabilidade
    roe = _safe_float(profitability.get("roe"))
    roic = _safe_float(profitability.get("roic"))
    
    # Solvência e Eficiência
    current_ratio = _safe_float(solvency.get("current_ratio"), default=1.0)
    net_margin = _safe_float(efficiency.get("net_margin"))
    nd_ebitda = _safe_float(solvency.get("net_debt_to_ebitda"))
    
    # Cash Flow e Crescimento
    ocf_to_ni = _safe_float(cash_flow.get("operating_cash_flow_to_net_income"), default=1.0) # Qualidade do Lucro
    fcf_margin = _safe_float(cash_flow.get("free_cash_flow_margin"), default=0.05)
    revenue_growth = _safe_float(growth.get("revenue_growth"))
    earnings_growth = _safe_float(growth.get("earnings_growth"))
    
    # Risco Estatístico
    beta = _safe_float(risk.get("beta"), default=1.0)

    # --- Roteamento Setorial Robusto ---
    sector = str(info.get("sector", "")).lower()
    industry = str(info.get("industry", "")).lower()
    
    is_utility = (
        "utilities" in sector or 
        "water" in industry or 
        "power" in industry or
        "energy" in sector
    )
    
    is_financial = (
        "financial" in sector or
        "bank" in industry or
        "insurance" in industry or
        "conglomerates" in industry or
        # Fallback de segurança na estrutura de dados enviada
        ("warning" in efficiency and "price_to_book" in valuation)
    )
    
    # Valuation e Preço
    pe_ratio = _safe_float(valuation.get("pe_ratio"))
    peg_ratio = _safe_float(valuation.get("peg_ratio"))
    
    if is_financial:
        valuation_metric = _safe_float(valuation.get("price_to_book"), default=1.5)
        is_expensive = valuation_metric > 2.0 or (pe_ratio > 15.0 and pe_ratio > 0)
        is_cheap = (valuation_metric < 1.0 and valuation_metric > 0) or (pe_ratio < 6.0 and pe_ratio > 0)
    else:
        valuation_metric = _safe_float(valuation.get("ev_to_ebitda"), default=10.0)
        # Inclusão Inteligente do PEG Ratio se disponível (crescimento do lucro mitigando o P/L)
        if peg_ratio > 0:
            is_expensive = (valuation_metric > 15.0) or (peg_ratio > 2.0)
            is_cheap = (valuation_metric < 6.0 and valuation_metric > 0) or (peg_ratio < 1.0)
        else:
            is_expensive = (valuation_metric > 15.0) or (pe_ratio > 25.0)
            is_cheap = (valuation_metric < 5.0 and valuation_metric > 0) or (pe_ratio < 10.0 and pe_ratio > 0)

    # Kill Switches de Risco Extremo
    bankruptcy_risk = bool(forensics.get("bankruptcy_risk", False))
    manipulation_risk = bool(forensics.get("manipulation_risk", False))

    # --- 4. MOTOR BASE (Fundamentos Contábeis) ---
    base_score = 5.0 # Ponto de partida (Neutro)

    # Avaliação de Lucro Econômico contra o Custo do Capital do Acionista
    if roic > wacc_proxy:
        base_score += 1.5 # Criação de Valor Real
    elif roic > 0 and roic < wacc_proxy:
        base_score -= 1.0 # Destruição Lenta de Patrimônio (Lucra menos que o CDI)
    elif roic < 0.0:
        base_score -= 2.0 # Prejuízo Queima de Caixa Operacional

    # A Qualidade Base do Lucro (Lucro precisa virar caixa, evita Accounting Fallacies)
    if ocf_to_ni < 0.5:
        base_score -= 1.0
    elif ocf_to_ni > 1.2:
        base_score += 0.5
        
    # --- 5. MATRIZ DINÂMICA (Precificada por Horizonte) ---
    
    # HORIZONTE ANO 1 (Sobrevivência, Volatilidade, Múltiplos)
    s1 = base_score
    if current_ratio < 1.0 and not is_utility:
        s1 -= 2.0 # Curto Prazo Sem Caixa vira Recuperação Judicial
    elif current_ratio > 1.5:
        s1 += 0.5
        
    if beta > 1.5:
        s1 -= 1.0 # Beta extremo sofre exageradamente no Curto Prazo
        
    if is_expensive and selic_esperada > 10.0:
        s1 -= 1.5 # Dinheiro não aceita desaforo na alta dos Juros
    elif is_cheap:
        s1 += 1.5
    s1 += (pib_esperado * 0.1)

    # HORIZONTE ANO 2 (Equilíbrio: Crescimento Acelerado vs Alavancagem)
    s2 = base_score
    if not is_financial and nd_ebitda > 3.0:
        s2 -= 1.5 # Dívida cara estrangula o pagamento de juros em 2y
        
    if earnings_growth > 0.10:
        s2 += 1.0 # Trajetória de EPS puxa o mercado
        
    if is_cheap:
        s2 += 1.0
    s2 += (pib_esperado * 0.15) - (ipca_esperado * 0.05)

    # HORIZONTE ANO 5 (A Prova do Negócio: Margem Média e Geração Livre de Caixa)
    s5 = base_score
    if net_margin > 0.10: # Meta relaxada p/ não penalizar certos setores como varejo de luxo
        s5 += 1.0
    elif net_margin < 0.03 and not is_financial:
        s5 -= 1.0
        
    if fcf_margin > 0.10:
        s5 += 1.0 # Dinheiro frio no bolso do acionista
        
    if roe > selic_decimal:
        s5 += 1.0
    s5 += (pib_esperado * 0.2)

    # HORIZONTE ANO 10 (Somente Negócios Excepcionais Sobrevivem Aqui)
    s10 = base_score
    if roic > wacc_proxy + 0.05:
        s10 += 3.0 # Vantagem Competitiva Monstruosa (Moat)
    elif roic > wacc_proxy:
        s10 += 1.0
    elif roic < 0.05:
        s10 -= 2.0 # Corrosão Crônica
        
    if revenue_growth > 0.10 and roic > wacc_proxy:
        s10 += 1.5 # Escalonamento Saudável (Cresce sem queimar margem)

    # --- 6. AGREGADORES E FILTROS FINAIS ---
    scores = [s1, s2, s5, s10]
    
    # Intervenção Forense (Nenhuma empresa maquiadora ganha passe livre)
    if bankruptcy_risk or manipulation_risk:
        scores = [min(s, 3.0) for s in scores]
        
    # Pós-processamento dos limites (0 estrito à 10 estrito) c/ Precisão Total até onde for possível
    scores = [max(0.0, min(10.0, float(s))) for s in scores]
    s1, s2, s5, s10 = scores
    
    # Global Score Equilibrado: Peso Focado na Construção Consistente
    # Diminuído as âncoras míopes e equilibrado em 1yr, 2yr e 5yr.
    global_score = (s1 * 0.15) + (s2 * 0.30) + (s5 * 0.35) + (s10 * 0.20)

    # O Output Final - O Primeiro (e único) momento de Arredondamento (para o Frontend)
    return {
        "global_score": float(np.round(global_score, 2)),
        "ano_1": float(np.round(s1, 2)),
        "ano_2": float(np.round(s2, 2)),
        "ano_5": float(np.round(s5, 2)),
        "ano_10": float(np.round(s10, 2))
    }
