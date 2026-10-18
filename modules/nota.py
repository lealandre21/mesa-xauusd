# -*- coding: utf-8 -*-
"""NOTA DA MESA: mede se as leituras do diário acertaram de verdade.

Honestidade metodológica:
- diario.csv anota a leitura a cada 5 min (fluxo_1h = alta/baixa/lateral).
- Pra cada HORA anotada com direção clara, olha 2 candles de 1h adiante e
  mede o delta real (fecho futuro vs abertura do momento).
- |delta| < US$ 0,50 = ruído (janela curta — não vira estatística de sorte).
- lateral não tem direção → não entra.
- Uma avaliação por candle (dedupe) — as 12 linhas/hora não duplo-contam.

Função pura `avaliar()` = sem rede, sem arquivo → 100% testável.
"""
import csv
import pathlib
from datetime import datetime, timedelta, timezone

from modules import data

_BRT = timezone(timedelta(hours=-3))
_CSV = pathlib.Path(__file__).parent.parent / "diario.csv"
_WINDOW = 2  # candles de 1h olhados pra frente
_NOISE = 0.5  # US$ abaixo disso é ruído

_Avaliacao = tuple[int, int, int, list[tuple[str, str, float, str]]]


def _linhas() -> list[dict]:
    try:
        with open(_CSV, encoding="utf-8", newline="") as f:
            return [r for r in csv.DictReader(f) if r.get("quando_brt")]
    except (OSError, UnicodeError):
        return []


def avaliar(linhas: list[dict], cand: list[dict]) -> _Avaliacao:
    """Lógica pura: (acertos, erros, ruidos, exemplos) — sem I/O."""
    acertos = erros = ruidos = 0
    exemplos: list[tuple[str, str, float, str]] = []
    vistos: set[int] = set()

    for r in linhas:
        direcao = (r.get("fluxo_1h") or "").strip().lower()
        if direcao not in ("alta", "baixa"):
            continue
        try:
            dt = datetime.strptime(r["quando_brt"].strip(), "%Y-%m-%d %H:%M")
        except (KeyError, ValueError):
            continue
        ts = int(dt.replace(tzinfo=_BRT).timestamp() * 1000)

        for i, c in enumerate(cand):
            if not (c["t"] <= ts < c["t"] + 3_600_000):
                continue
            j = i + _WINDOW
            if j >= len(cand):
                break  # futuro ainda não fechou
            if c["t"] in vistos:
                break  # já avaliei essa hora
            vistos.add(c["t"])

            delta = cand[j]["c"] - c["o"]
            if abs(delta) < _NOISE:
                ruidos += 1
                break
            ok = (delta > 0 and direcao == "alta") or (delta < 0 and direcao == "baixa")
            acertos += 1 if ok else 0
            erros += 0 if ok else 1
            exemplos.append(
                (r["quando_brt"], direcao, round(delta, 2), "✅" if ok else "❌")
            )
            break

    return acertos, erros, ruidos, exemplos


def resumo() -> tuple[str, list[tuple[str, str, float, str]]]:
    """(texto da nota, exemplos recentes) — lê arquivo + rede e delega a avaliar()."""
    linhas = _linhas()
    if not linhas:
        return "🤔 Sem registros no diário ainda — deixa a Mesa aberta de dia e volta.", []

    cand = data.candles("1h", 200)
    if not cand:
        return "📉 Sem candles agora pra medir (rede?).", []

    acertos, erros, ruidos, exemplos = avaliar(linhas, cand)
    total = acertos + erros
    if total == 0:
        return (
            f"⏳ Chamadas ainda aguardando o futuro: os {_WINDOW} candles de 1h "
            f"depois das anotações precisam FECHAR pra nota sair "
            f"({ruidos} ruídos filtrados). Deixa a mesa aberta — amanhã tem nota."
        ), []

    pct = round(100 * acertos / total)
    nota = (
        f"🎯 **{pct}% de acerto** · {acertos}/{total} chamadas claras · "
        f"{ruidos} ruídos (movimento < US$ {_NOISE:.2f})\n\n"
        f"🪞 janela: {_WINDOW} candles de 1h pra frente · amostra: horas do diário"
    )
    return nota, exemplos[-6:][::-1]
