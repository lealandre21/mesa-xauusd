# -*- coding: utf-8 -*-
"""Scanner multimercado: enquanto o ouro não dá setup, a gente vigia outros.

Proxys na Binance: ouro PAXGUSDT + BTC/ETH/SOL/EUR.
Cada linha responde: direção (15m+1h batem?), tem FVG?, preço caro ou barato?
Educacional — não é recomendação de mercado nenhum.
"""
import streamlit as st

from modules import smc

SYMBOLS = [
    ("PAXGUSDT", "🥇 Ouro (XAU)", True),
    ("BTCUSDT", "₿ Bitcoin", False),
    ("ETHUSDT", "Ξ Ethereum", False),
    ("SOLUSDT", "◎ Solana", False),
    ("EURUSDT", "€ Euro", False),
]


@st.cache_data(ttl=60, show_spinner=False)
def _klines(symbol, interval="1h", limit=80):
    from modules import data
    d = data._try(
        f"https://api.binance.com/api/v3/klines"
        f"?symbol={symbol}&interval={interval}&limit={limit}"
    )
    return [
        {"t": int(k[0]), "o": float(k[1]), "h": float(k[2]),
         "l": float(k[3]), "c": float(k[4])}
        for k in (d or [])
    ]


def _scan_symbol(symbol):
    c1 = _klines(symbol, "1h", 80)
    c15 = _klines(symbol, "15m", 96)
    if not c1 or not c15:
        return None
    t1 = smc._trend(c1)
    t15 = smc._trend(c15)
    alinhado = t1 == t15 and t1 != "lateral"
    fv = smc._recent_fvgs(c15)
    fvg_txt = f"{fv[-1][0].capitalize()} {smc.data.fmt(min(fv[-1][1], fv[-1][2]))}" if fv else "—"
    hi = max(x["h"] for x in c1[-20:])
    lo = min(x["l"] for x in c1[-20:])
    pos = (c1[-1]["c"] - lo) / (hi - lo) * 100 if hi > lo else 50
    direcao = t1 if alinhado else f"{t1}/15m:{t15}"
    return {
        "Direção": direcao,
        "FVG 15m": fvg_txt,
        "Faixa": f"{pos:.0f}% da faixa",
        "Alinhado": "✔" if alinhado else "✘",
        "_alinhado": alinhado,
        "_pos": pos,
    }


@st.cache_data(ttl=90, show_spinner=False)
def scan():
    out = []
    for symbol, nome, foco in SYMBOLS:
        r = _scan_symbol(symbol)
        if r:
            r["Par"] = nome
            r["Foco Ouro"] = "🎯" if foco else ""
            out.append(r)
    ordem = ["Foco Ouro", "Par", "Direção", "FVG 15m", "Faixa", "Alinhado"]
    return [{k: r[k] for k in ordem} for r in out]


def foco_alternativo():
    """Primeiro par alinhado (não-ouro) com faixa em extremo."""
    for symbol, nome, foco in SYMBOLS:
        if foco:
            continue
        r = _scan_symbol(symbol)
        if r and r["Alinhado"] == "✔" and (r["_pos"] <= 35 or r["_pos"] >= 65):
            return nome, r["Direção"], r["Faixa"]
    return None
