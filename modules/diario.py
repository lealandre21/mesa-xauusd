# -*- coding: utf-8 -*-
"""Diário automático: grava a leitura da mesa a cada 5 minutos em diario.csv.

Serve pro aluno comparar depois: o que a mesa pensava às 02h vs o que o
mercado fez. Cru e simples — histórico é ouro pra estudar.
"""
import csv
import os
from datetime import datetime, timedelta, timezone

from modules import calendar, dashboard, plan, smc
from modules import data

_BRT = timezone(timedelta(hours=-3))
_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "diario.csv")
_CAMPOS = [
    "quando_brt", "preco", "sessao", "fluxo_4h", "fluxo_1h", "fluxo_15m",
    "bos", "choch", "faixa_porc", "plano", "alvo", "proximo_evento",
]


def _ultima_hora():
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            linhas = [l for l in f.read().strip().splitlines() if l.strip()]
            if len(linhas) > 1:
                return linhas[-1].split(",")[0]
    except OSError:
        pass
    return ""


def log():
    """Anota uma linha (máx. 1 por 5 minutos)."""
    agora = datetime.now(_BRT)
    iso = agora.strftime("%Y-%m-%d %H:%M")
    ultima = _ultima_hora()
    if ultima:
        try:
            anterior = datetime.strptime(ultima, "%Y-%m-%d %H:%M").replace(tzinfo=_BRT)
            delta = agora - anterior
            if delta.total_seconds() < 300:
                return False
        except ValueError:
            pass

    p = plan.plano()
    preco = data.price()
    evos = calendar.upcoming(True)
    evos_txt = f"{evos[0]['Quando']} {evos[0]['Evento']}" if evos else ""

    novo = not os.path.exists(_PATH)
    try:
        with open(_PATH, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if novo:
                w.writerow(_CAMPOS)
            w.writerow([
                iso,
                data.fmt(preco) if preco else "",
                dashboard.current_session(),
                p["trends"][0], p["trends"][1], p["trends"][2],
                smc.detect_bos(), smc.detect_choch(),
                smc.pd_state()[0],
                p["headline"],
                data.fmt(p["alvo"]) if p["alvo"] else "",
                evos_txt,
            ])
        return True
    except OSError:
        return False
