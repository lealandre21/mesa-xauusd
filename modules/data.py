# -*- coding: utf-8 -*-
"""Fonte de dados reais, sem chave de API.
- Spot do ouro: gold-api.com
- Candles: Binance PAXGUSDT (PAXG é ouro tokenizado 1:1, proxy do XAUUSD)
- Bid/Ask: Binance (para spread)
Tudo com cache (st.cache_data) pra não martelar a API a cada clique.
Conteúdo educacional — não é recomendação.
"""
import json
import urllib.request

import streamlit as st

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


@st.cache_data(ttl=15, show_spinner=False)
def _get_json(url: str):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def _try(url: str):
    try:
        return _get_json(url)
    except Exception:
        return {}


def spot():
    """Preço à vista do ouro (USD) ou None."""
    d = _try("https://api.gold-api.com/price/XAU")
    try:
        return float(d["price"])
    except (KeyError, TypeError, ValueError):
        return None


@st.cache_data(ttl=30, show_spinner=False)
def _binance_candles(interval: str = "15m", limit: int = 100):
    """Klines da Binance PAXGUSDT (proxy) com volume comprador incluído."""
    d = _try(
        f"https://api.binance.com/api/v3/klines"
        f"?symbol=PAXGUSDT&interval={interval}&limit={limit}"
    )
    out = []
    for k in d or []:
        out.append(
            {
                "t": int(k[0]),
                "o": float(k[1]),
                "h": float(k[2]),
                "l": float(k[3]),
                "c": float(k[4]),
                "v": float(k[5]),        # volume total do candle
                "vb": float(k[9]),       # volume comprado por compradores agressivos (taker buy)
            }
        )
    return out


@st.cache_data(ttl=30, show_spinner=False)
def candles(interval: str = "15m", limit: int = 100):
    """Candles da Mesa: PREFERE o MT5 (broker real); fallback Binance."""
    from modules import mt5_data
    try:
        dados = mt5_data.candles(interval, limit)
        if dados:
            return dados
    except Exception:
        pass
    return _binance_candles(interval, limit)


@st.cache_data(ttl=90, show_spinner=False)
def candles_binance(interval: str = "15m", limit: int = 100):
    """Versão FIXEDA na Binance — usada pra pressão de volume (agressão)."""
    return _binance_candles(interval, limit)


def book():
    """Bid/ask: PREFERE o broker real (MT5); fallback Binance."""
    from modules import mt5_data
    t = mt5_data.tick()
    if t and t.get("bid") and t.get("ask"):
        try:
            return float(t["bid"]), float(t["ask"])
        except (TypeError, ValueError):
            pass
    d = _try("https://api.binance.com/api/v3/ticker/bookTicker?symbol=PAXGUSDT")
    try:
        return float(d["bidPrice"]), float(d["askPrice"])
    except (KeyError, TypeError, ValueError):
        return None, None


def last_close(interval: str = "1m"):
    c = candles(interval, 2)
    return c[-1]["c"] if c else None


def price():
    """Spot real, com fallback pro proxy da Binance."""
    s = spot()
    if s is not None:
        return s
    return last_close("1m")


def fmt(v) -> str:
    try:
        return f"{float(v):,.2f}"
    except (TypeError, ValueError):
        return "-"
