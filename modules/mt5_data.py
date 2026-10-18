# -*- coding: utf-8 -*-
"""Cliente Mesa → ponte MT5 (http://127.0.0.1:8600).

Tudo com timeout curto: se a ponte estiver desligada, as funções retornam
None e quem chama cai no fallback (Binance/gold-api) sem drama.
"""
import json
import urllib.error
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


def demo():
    """True se a conta logada é DEMO ( haste anti-real)."""
    d = acct()
    return bool(d and d.get("demo"))


def risco():
    """(volume_min, tick_value, tick_size) do símbolo vivo ou None."""
    d = _get("/sym")
    if d and d.get("conectado"):
        return d["volume_min"], d["tick_value"], d["tick_size"]
    return None


def positions():
    """Posições abertas no símbolo do ouro (lista) ou None se ponte morta."""
    d = _get("/positions")
    if d is None:
        return None
    return d.get("positions") or []


def enviar(direcao: str, lote: float, sl: float, tp=None):
    """Envia ordem a mercado com SL (barra anti-real na ponte)."""
    return _post("/order", {"direcao": direcao, "lote": lote,
                            "sl": sl, "tp": tp or None})


def fechar(ticket: int):
    """Fecha posição pelo ticket."""
    return _post("/close", {"ticket": int(ticket)})


def deals():
    """Resultados realizados das últimas 24h (com lucro por ticket)."""
    d = _get("/deals")
    return d.get("deals") if d and d.get("conectado") else None


def _post(path, corpo: dict):
    req = urllib.request.Request(
        URL + path,
        data=json.dumps(corpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read().decode("utf-8"))
    except (OSError, ValueError, urllib.error.HTTPError) as e:
        try:
            return json.loads(getattr(e, "read", lambda: b"")().decode("utf-8"))
        except (ValueError, OSError):
            return {"erro": str(e)}
