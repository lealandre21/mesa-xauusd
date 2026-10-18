# -*- coding: utf-8 -*-
"""Métricas de mercado com dados reais (proxy PAXG/ouro à vista)."""
from modules import data, smc


def current_price():
    p = data.price()
    if p is None:
        return "-"
    return f"US$ {data.fmt(p)}"


def spread():
    bid, ask = data.book()
    if bid is None or ask is None or ask <= 0:
        return "-"
    return f"US$ {data.fmt(ask - bid)}"


def probability():
    """Confiança heurística por alinhamento HTF x LTF (educacional)."""
    return f"{smc.alignment_score()}%"


def target():
    t = smc.next_target()
    if t is None:
        return "-"
    return f"US$ {data.fmt(t)}"


def market_status():
    return smc.mkt_status()
