# -*- coding: utf-8 -*-
"""Calculadora completa: R:R, pips e dinheiro no bolso (educacional).

XAUUSD: 1 pip = 0.10 de preço · 1 lote = 100 oz => US$ 10 por pip.
Ajuste o tamanho de lote se sua corretora for diferente.
"""
PIP = 0.1
VALOR_PIP_POR_LOTE = 10.0  # US$ por pip por lote (padrão XAUUSD)


def _valida(entry, stop, take):
    if not entry or not stop or not take:
        return "Preencha os 3 valores"
    if entry == stop:
        return "Entrada = stop, confira"
    longo = entry > stop
    ok = (take > entry) if longo else (take < entry)
    if not ok:
        return "⚠Stop/Take no lado errado (confira)"

def calculate_rr(entry, stop, take):
    falha = _valida(entry, stop, take)
    if falha:
        return "—"
    risco = abs(entry - stop)
    premio = abs(take - entry)
    return f"1 : {premio / risco:.2f}"


def calculate_money(entry, stop, take, lots=1.0):
    """Dict com R:R, pips e dólares (uma posição com 'lots' lotes)."""
    falha = _valida(entry, stop, take)
    if falha:
        return {"erro": "—"}
    risco = abs(entry - stop)
    premio = abs(take - entry)
    pips_risco = risco / PIP
    pips_premio = premio / PIP
    return {
        "rr": f"1 : {premio / risco:.2f}",
        "pips_risco": round(pips_risco, 1),
        "pips_premio": round(pips_premio, 1),
        "dol_risco": round(pips_risco * VALOR_PIP_POR_LOTE * lots, 2),
        "dol_premio": round(pips_premio * VALOR_PIP_POR_LOTE * lots, 2),
    }
