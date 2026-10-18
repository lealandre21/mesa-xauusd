# -*- coding: utf-8 -*-
"""Sessão (horário de Brasília, UTC-3), confiança e estado do mercado.

Killzones conforme o currículo de estudo:
- Ásia 21h–1h | LOKZ 3h–6h | NYOKZ 8h–11h | LCKZ 11h–13h (Brasília)
"""
from datetime import datetime, timedelta, timezone

from modules import smc

_BRT = timezone(timedelta(hours=-3))


def _hora_brt():
    return datetime.now(_BRT)


def hora_brt():
    """Hora de Brasília pública (o chat usa)."""
    return _hora_brt()


def current_session():
    h = _hora_brt().hour
    if 21 <= h or h < 1:
        return "Ásia (21h–1h)"
    if 3 <= h < 6:
        return "Londres (LOKZ)"
    if 8 <= h < 11:
        return "NY (NYOKZ)"
    if 11 <= h < 13:
        return "Tardinha (LCKZ)"
    if 1 <= h < 3:
        return "Pré-Londres"
    return "Fora de killzone"


def confidence():
    return f"{smc.alignment_score()}%"


def market_state():
    txt, _pos = smc.pd_state()
    return txt


def mercado_fx():
    """(aberto?, texto de abertura) — horário real do XAUUSD em Brasília.
    Fecha sex ~20h BRT, reabre dom 21h BRT (aprox.= horário de verão NY)."""
    agora = _hora_brt()
    wd, h = agora.weekday(), agora.hour  # seg=0 ... dom=6
    if wd == 5:
        return False, "abre domingo 21h"
    if wd == 6 and h < 21:
        return False, "abre hoje 21h"
    if wd == 4 and h >= 20:
        return False, "abre domingo 21h"
    return True, "aberto"
