# -*- coding: utf-8 -*-
"""Motor de indicadores técnicos da Mesa.

TUDO aqui é CONFIRMAÇÃO/contexto de leitura — nunca sinal de ordem.
SMC continua a bússola da mesa; RSI/ATR/pressão são termômetros.

Fórmulas puras (lista de dicts/floats → resultado) para testes fáceis.
Cálculos clássicos de Wilder. Conteúdo educacional — conta demo sempre.
"""

# ------ Pure math ----------------------------------------------------------

def rsi(closes, periodo: int = 14):
    """RSI de Wilder. Recebe lista de fechamentos → float ou None."""
    if len(closes) < periodo + 1:
        return None
    ganhos, perdas = [], []
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i - 1]
        ganhos.append(max(delta, 0.0))
        perdas.append(max(-delta, 0.0))
    media_g = sum(ganhos[:periodo]) / periodo
    media_p = sum(perdas[:periodo]) / periodo
    for i in range(periodo, len(ganhos)):
        media_g = (media_g * (periodo - 1) + ganhos[i]) / periodo
        media_p = (media_p * (periodo - 1) + perdas[i]) / periodo
    if media_p == 0:
        return 100.0
    rs = media_g / media_p
    return 100.0 - (100.0 / (1.0 + rs))


def atr(candles, periodo: int = 14):
    """ATR de Wilder (média do alcance real). Recebe candles → float ou None."""
    if len(candles) < periodo + 1:
        return None
    trs = []
    for i in range(1, len(candles)):
        h, l, c_ant = candles[i]["h"], candles[i]["l"], candles[i - 1]["c"]
        trs.append(max(h - l, abs(h - c_ant), abs(l - c_ant)))
    a = sum(trs[:periodo]) / periodo
    for i in range(periodo, len(trs)):
        a = (a * (periodo - 1) + trs[i]) / periodo
    return a


def pressao(candles, n: int = 20):
    """Pressão comprador × vendedor (agressividade no volume, não no preço).

    Binance fornece 'vb' = volume comprado por compradores agressivos.
    O resto do volume 'v' é tratado como agressão vendedora (aprox. padrão de
    mercado). Retorna (pct_comprador, pct_vendedor) ou None.
    """
    ult = candles[-n:]
    vb = sum(c.get("vb", 0.0) for c in ult)
    tot = sum(c.get("v", 0.0) for c in ult)
    if tot <= 0 or vb <= 0:
        return None  # sem dado de agressão compradora → "sem dados" (nunca inventar)
    pc = 100.0 * vb / tot
    return pc, 100.0 - pc


# ------ Textos de leitura (educacionais, sem recomendação) -----------------

def txt_rsi(valor):
    if valor is None:
        return "sem dados suficientes"
    if valor >= 70:
        return "exaltado — força, mas perto do exagero histórico"
    if valor >= 55:
        return "comprador dominando o curtinho"
    if valor >= 45:
        return "terreno neutro — ninguém dita o ritmo"
    if valor >= 30:
        return "vendedor dominando o curtinho"
    return "esgotado — força vendedora quebrando, olho em reação"


def txt_atr(valor, preco):
    """Leitura de volatilidade pelo % que o ATR representa do preço."""
    if valor is None or not preco:
        return "sem dados suficientes"
    pct = 100.0 * valor / float(preco)
    if pct < 0.12:
        return "mercado quieta (pavio curto) — períodos de lateral"
    if pct <= 0.32:
        return "volatilidade saudável — movimento com respiração"
    return "mercado QUENTE — alta energia, stop mais generoso"


def txt_pressao(pct_comprador):
    if pct_comprador is None:
        return "sem dados suficientes"
    if pct_comprador >= 55:
        return "compradores agressivos puxando o volume"
    if pct_comprador >= 45:
        return "volume repartido — briga de faixa curta"
    return "vendedores agressivos pressionando o volume"


# ------ Wrapper da mesa ----------------------------------------------------

def leitura(tf: str = "15m", preco=None):
    """Junta tudo a partir dos candles reais da Mesa → dict pronto pra UI."""
    from modules import data

    cs = data.candles(tf, 100)
    closes = [c["c"] for c in cs]
    r = rsi(closes)
    a = atr(cs)
    # pressão lê a Binance (única fonte com agressão compradora separada)
    pc = pressao(data.candles_binance(tf, 40))
    preco = preco if preco is not None else data.price()
    return {
        "rsi": r,
        "rsi_txt": txt_rsi(r),
        "atr": a,
        "atr_txt": txt_atr(a, preco),
        "press": pc,
        "press_txt": txt_pressao(pc[0] if pc else None),
    }
