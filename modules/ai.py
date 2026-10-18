# -*- coding: utf-8 -*-
"""Resumo geral da IA da mesa — saída baseada nos indicadores reais."""
from modules import dashboard, smc


def market_analysis():
    b = smc.detect_bias()
    ch = smc.detect_choch()
    liq = smc.detect_liquidity()
    appo, _pos = smc.pd_state()
    sess = dashboard.current_session()
    return f"""
Viés de estrutura (1h): {b} · CHoCH: {ch}

Faixa atual: {appo}

Liquidez: {liq}

Sessão: {sess} · Confiança heurística: {dashboard.confidence()}

Leitura: seguia o fluxo do HTF e esperar o LTF entregar a zona.
""".replace("<br>", "\n")
