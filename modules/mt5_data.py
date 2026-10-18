# -*- coding: utf-8 -*-
"""Cliente Mesa → ponte MT5 (http://127.0.0.1:8600).

Tudo com timeout curto: se a ponte estiver desligada, as funções retornam
None e quem chama cai no fallback (Binance/gold-api) sem drama.
"""
import json
import urllib.request

URL = "http://127.0.0.1:8600"
TO = 2.5


def _get(path):
    try:
        with urllib.request.urlopen(URL + path, timeout=TO) as r:
            return json.loads(r.read().decode("utf-8"))
    except (OSError, ValueError):
        return None


def alive():
    return bool(_get("/health"))


def acct():
    """Conta/servidor/saldo do terminal logado ou None."""
    d = _get("/acct")
    return d if (d and d.get("conectado")) else None


def tick():
    """Bid/ask do broker real (escolhe símbolo vivo sozinho) ou None."""
    d = _get("/tick")
    return d if (d and d.get("conectado")) else None


def candles(tf: str = "15m", limit: int = 100):
    """Candles do broker real no formato da Mesa (t,o,h,l,c,v,vb) ou None."""
    d = _get(f"/candles?tf={tf}&n={limit}")
    if d and d.get("conectado"):
        return d.get("candles") or []
    return None
