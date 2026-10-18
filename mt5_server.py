# -*- coding: utf-8 -*-
"""Ponte MT5 → JSON (parte da Mesa XAUUSD).

Roda com Python 3.12 (o pacote MetaTrader5 não tem wheel pra 3.15).
Fala com o terminal MT5 ABERTO/LOGADO — nunca pede senha.
Escuta apenas em 127.0.0.1 (a internet de fora não vê nada).

Rotas:
  /acct            → conta/servidor/saldo
  /tick            → bid/ask/spread/último do XAUUSD (fonte: broker real)
  /candles?tf=15m&n=100 → candles OHLC+volume no mesmo formato da Mesa

Escolha de símbolo: XAUUSDm por padrão; se ele estiver parado (mercado
frechinho/fim de semana), cai pra XAUUSD247m (quase 24/7 na Exness).
"""
import json
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import MetaTrader5 as mt5

PORTA = 8600
PREFERIDOS = ["XAUUSDm", "XAUUSD247m", "XAUUSD"]
MAPA_TF = {"1m": mt5.TIMEFRAME_M1, "5m": mt5.TIMEFRAME_M5, "15m": mt5.TIMEFRAME_M15,
           "1h": mt5.TIMEFRAME_H1, "4h": mt5.TIMEFRAME_H4}
STALE = 15 * 60  # segundos: tick mais velho que isso → tenta o 247


def escolhe_simbolo():
    """Primeiro preferido com pulso recente; senão o segundo."""
    for nome in PREFERIDOS:
        s = mt5.symbol_info(nome)
        if s is None:
            continue
        mt5.symbol_select(nome, True)
        t = mt5.symbol_info_tick(nome)
        if t and t.time and t.time > time.time() - STALE:
            return nome, t
    # ninguém pulsa (domingo antes da abertura)? último pulso que der
    for nome in PREFERIDOS:
        t = mt5.symbol_info_tick(nome)
        if t and t.time:
            return nome, t
    return None, None


def rates_para_candles(rates):
    """Rates do MT5 → lista de dicts (t em ms like Binance)."""
    out = []
    for r in rates:
        out.append({
            "t": int(r["time"]) * 1000,
            "o": float(r["open"]),
            "h": float(r["high"]),
            "l": float(r["low"]),
            "c": float(r["close"]),
            "v": float(r["tick_volume"]),
            "vb": 0.0,  # MT5 não separa agressão compradora → pressão usa proxy Binance
        })
    return out


class Handler(BaseHTTPRequestHandler):

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        partes = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(partes.query)
        try:
            if partes.path == "/acct":
                a = mt5.account_info()
                self._json({
                    "conectado": bool(a),
                    "login": a.login if a else None,
                    "servidor": a.server if a else None,
                    "moeda": a.currency if a else None,
                    "saldo": a.balance if a else None,
                })
            elif partes.path == "/tick":
                nome, t = escolhe_simbolo()
                if not t:
                    self._json({"conectado": False}, 503)
                    return
                mid = (t.bid + t.ask) / 2 if t.ask and t.bid else t.last
                self._json({
                    "conectado": True,
                    "symbol": nome,
                    "bid": t.bid, "ask": t.ask,
                    "spread": round(t.ask - t.bid, 5) if (t.bid and t.ask) else None,
                    "last": t.last or mid,
                    "t": t.time * 1000,
                })
            elif partes.path == "/candles":
                nome, _ = escolhe_simbolo()
                if not nome:
                    self._json({"conectado": False}, 503)
                    return
                tf = MAPA_TF.get(qs.get("tf", ["15m"])[0], mt5.TIMEFRAME_M15)
                n = min(int(qs.get("n", ["100"])[0]), 500)
                rates = mt5.copy_rates_from_pos(nome, tf, 0, n)
                if rates is None:
                    self._json({"conectado": False, "erro": mt5.last_error()}, 503)
                    return
                self._json({"conectado": True, "symbol": nome, "candles": rates_para_candles(rates)})
            elif partes.path == "/health":
                self._json({"vivo": True, "agora": datetime.now(timezone.utc).isoformat()})
            else:
                self._json({"erro": "rota desconhecida"}, 404)
        except (ValueError, KeyError, ConnectionError, OSError) as e:
            self._json({"erro": str(e)}, 500)


if __name__ == "__main__":
    if not mt5.initialize():
        print("MT5 não conectou:", mt5.last_error(), file=sys.stderr)
        sys.exit(1)
    a = mt5.account_info()
    print("MT5 ligado · conta", a.login if a else "?", "·", a.server if a else "?")
    serv = ThreadingHTTPServer(("127.0.0.1", PORTA), Handler)
    print(f"Ponte MT5 escutando em http://127.0.0.1:{PORTA} — Ctrl+C desliga")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        mt5.shutdown()
