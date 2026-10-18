# -*- coding: utf-8 -*-
"""Mesa de analistas — os textos SAEM dos indicadores reais (modules.smc).

Cada analista só enxerga "o seu" recorte. O moderador resume tudo
numa decisão educacional. Sem IA paga, sem chave — regra + dado real.
"""
from modules import data, smc, dashboard


def smc_analyst():
    b = smc.detect_bias()
    bos = smc.detect_bos()
    ch = smc.detect_choch()
    liq = smc.detect_liquidity()
    return f"""
**Estrutura de Mercado** (1h)

Viés: {b}

{bos} · CHoCH: {ch}

Liquidez: {liq}
"""


def ict_analyst():
    fv = smc.detect_fvg()
    ob = smc.detect_orderblock()
    pd_txt, pos = smc.pd_state()
    pend = "sem gap ativo" if fv in ("Nenhum ativo", "-") else f"gap {fv}"
    return f"""
**Conceitos ICT** (15m + 1h)

FVG: {pend}

Order Block: {ob}

Faixa: {pd_txt}
"""


def quant_analyst():
    conf = smc.alignment_score()
    b4 = smc._trend(data.candles("4h", 40))
    b15 = smc._trend(data.candles("15m", 96))
    alinhado = "✔ alinhado" if b4 == b15 else "✘ divergente"
    return f"""
**Probabilidade (heurística)**

Confiança: {conf}% · HTF(4h) x LTF(15m): {alinhado}

Amostra pequena = sinal fraco. Espere confirmação (regra dos 70%).
"""


def risk_manager():
    bsl, ssl, _eqh, _eql = smc.liquidity_map()
    p = data.price()
    if p is None or bsl is None or ssl is None:
        return "**Gestão de Risco**\n\nSem mapa de liquidez — calcule stop manualmente."
    risco_ate_ssl = abs(p - ssl)
    alvo_ate_bsl = abs(bsl - p)
    rr = alvo_ate_bsl / risco_ate_ssl if risco_ate_ssl > 0 else 0
    return f"""
**Gestão de Risco (mapa atual)**

Stop atrás do SSL: {data.fmt(ssl)} (risco ≈ US$ {data.fmt(risco_ate_ssl)})

Alvo no BSL: {data.fmt(bsl)} (prêmio ≈ US$ {data.fmt(alvo_ate_bsl)})

Potencial: 1 : {rr:.2f}
"""


def moderator():
    conf = smc.alignment_score()
    pd_txt, pos = smc.pd_state()
    if conf >= 75 and pos < 45:
        decide = "CONTINUAÇÃO POSSÍVEL — aguardar confirmação do retrocesso"
    elif conf >= 75 and pos > 55:
        decide = "AGUARDAR RETROCESSO — preço caro na faixa"
    else:
        decide = "DE FORA — alinhamento fraco, deixe o mercado mostrar"
    return f"""
**DECISÃO FINAL ( educacional)**

{decide}

Confiança: {conf}% · Sessão: {dashboard.current_session()} · Faixa: {pd_txt}

Nada aqui é recomendação — treine na **conta demo**.
"""
