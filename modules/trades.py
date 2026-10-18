# -*- coding: utf-8 -*-
"""Modo Conta Demo: cartão de execução assistida da Mesa.

Tudo nasce do PLANO (entrada = mercado no momento do clique, stop = estrutura
BSL/SSL com respiração de ATR, alvo = next_target do plano). Lote fixo pequeno.
Regras de casa:
- Só conta DEMO (a ponte bloqueia qualquer coisa real).
- Stop obrigatório, NUNCA ordem sem invalidação.
- Cada envio entra no trades.csv (histórico pra Nota da Mesa).
Educacional — não é recomendação.
"""
import csv
import os
from datetime import datetime, timezone, timedelta

from modules import data, plan, smc

CSV_TRADES = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trades.csv")
BRT = timezone(timedelta(hours=-3))


def direcao_do_plano(p=None):
    """'compra'/'venda' de acordo com a leitura, ou None se 'DE FORA'."""
    p = p or plan.plano()
    h = p["headline"].upper()
    if "COMPRA" in h or h.startswith("ALINHADO ALTA"):
        return "compra"
    if "VENDA" in h or h.startswith("ALINHADO BAIXA"):
        return "venda"
    return None


def _atr15():
    from modules import indicadores
    try:
        return indicadores.atr(data.candles_binance("15m", 40)) or 2.0
    except Exception:
        return 2.0


def cartao(preco=None):
    """Cartão de execução → dict ou None (sem setup válido).

    stop = nível estrutural (BSL p/ venda, SSL p/ compra) ± sobra de ATR.
    stint ssao de estrutura? respiração de 1.5×ATR em volta do preço.
    """
    p = plan.plano()
    direcao = direcao_do_plano(p)
    if direcao is None:
        return {"sem_setup": True, "headline": p["headline"]}

    preco = preco if preco is not None else (data.price() or 0)
    if not preco:
        return {"sem_setup": True, "headline": p["headline"]}

    bsl, ssl, _eqh, _eql = smc.liquidity_map()
    a = _atr15()
    sobra = 0.6 * a

    if direcao == "compra":
        stop = (ssl - sobra) if ssl else (preco - 1.5 * a)
        stop = min(stop, preco - 0.25 * a)  # stop nunca acima do preço
    else:
        stop = (bsl + sobra) if bsl else (preco + 1.5 * a)
        stop = max(stop, preco + 0.25 * a)
    stop = round(stop, 2)

    alvo = p["alvo"]
    risco = abs(preco - stop)
    if not alvo or risco <= 0:
        alvo = preco + 2.0 * risco if direcao == "compra" else preco - 2.0 * risco
    else:
        alvo = float(alvo)
    try:
        rr = abs(alvo - preco) / risco if risco > 0 else None
    except ZeroDivisionError:
        rr = None
    if rr is not None and rr < 1.0:
        return {"sem_setup": False, "rr_baixo": rr, "headline": p["headline"],
                "direcao": direcao, "preco": preco, "stop": stop, "alvo": alvo}

    return {
        "sem_setup": False, "headline": p["headline"],
        "gatilho": p["gatilho"], "invalida_txt": p["invalidacao"],
        "direcao": direcao, "preco": round(float(preco), 2),
        "stop": stop, "alvo": round(float(alvo), 2),
        "risco": round(risco, 2), "rr": round(rr, 2) if rr else None,
    }


def risco_dinheiro(preco, stop, tick_value=None, tick_size=None, lote=0.01):
    """US$ em jogo pela distância entrada→stop (usa dados reais do broker)."""
    try:
        if not tick_value or not tick_size:
            # padrão XAUUSD: 0.01 lote ≈ US$ 1,00 por US$1 de movimento
            return abs(preco - stop) * 1.0 * (lote / 0.01)
        return abs(preco - stop) / tick_size * tick_value * lote
    except (TypeError, ZeroDivisionError):
        return None


def registra(registro: dict):
    """Anexa a entrada ao trades.csv (histórico p/ Nota da Mesa)."""
    existe = os.path.exists(CSV_TRADES)
    campos = ["quando", "tipo", "symbol", "direcao", "lote", "entrada",
              "stop", "alvo", "plano", "ticket"]
    with open(CSV_TRADES, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        if not existe:
            w.writeheader()
        linha = {k: registro.get(k, "") for k in campos}
        w.writerow(linha)


def agora():
    return datetime.now(BRT).strftime("%d/%m %H:%M")
