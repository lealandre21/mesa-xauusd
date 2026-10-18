# -*- coding: utf-8 -*-
"""Detecção de SMC com candles reais.

Regras que seguem o currículo de estudo:
- BoS só com CORPO rompendo (pavio não conta — vira sweep/fake).
- Viés = HH/HL (alta) ou LH/LL (baixa) pelos últimos swings.
- Premium/Discount pela faixa dos últimos 20 candles (50% = equilíbrio).
Só leitura — nada disso é sinal de ordem.
"""
from modules import data


def _swings(c, lb=2):
    """Swings por fractal simples (lookback lb pra cada lado)."""
    highs, lows = [], []
    for i in range(lb, len(c) - lb):
        w = c[i - lb : i + lb + 1]
        if c[i]["h"] >= max(x["h"] for x in w):
            highs.append(c[i]["h"])
        if c[i]["l"] <= min(x["l"] for x in w):
            lows.append(c[i]["l"])
    return highs, lows


def _trend(c):
    """'alta' | 'baixa' | 'lateral' a partir dos 2 últimos topos e fundos."""
    highs, lows = _swings(c)
    if len(highs) < 2 or len(lows) < 2:
        return "lateral"
    h2, h1 = highs[-1], highs[-2]
    l2, l1 = lows[-1], lows[-2]
    if h2 > h1 and l2 > l1:
        return "alta"
    if h2 < h1 and l2 < l1:
        return "baixa"
    return "lateral"


_TXT = {"alta": "Alta (HH + HL)", "baixa": "Baixa (LH + LL)", "lateral": "Lateral / Mista"}


def detect_bias():
    c = data.candles("1h", 80)
    if not c:
        return "-"
    return _TXT[_trend(c)]


def detect_bos():
    """BoS pelo FECHAMENTO (corpo) rompendo o swing anterior."""
    c = data.candles("1h", 80)
    if len(c) < 5:
        return "-"
    highs, lows = _swings(c)
    ult = c[-1]["c"]
    if len(highs) >= 2 and ult > highs[-2]:
        return f"BoS de alta (corpo rompeu {data.fmt(highs[-2])})"
    if len(lows) >= 2 and ult < lows[-2]:
        return f"BoS de baixa (corpo rompeu {data.fmt(lows[-2])})"
    return "Sem novo BoS"


def detect_choch():
    """CHoCH = tendência da metade antiga diferente da metade recente."""
    c = data.candles("1h", 80)
    if len(c) < 20:
        return "Não"
    meio = len(c) // 2
    antiga = _trend(c[:meio])
    recente = _trend(c[meio:])
    if antiga != recente and antiga in ("alta", "baixa"):
        return f"Sim ({antiga} → {recente})"
    return "Não"


def _recent_fvgs(c, look=40):
    out = []
    n = len(c)
    for i in range(max(2, n - look), n):
        if c[i]["l"] > c[i - 2]["h"]:
            out.append(("alta", c[i - 2]["h"], c[i]["l"]))
        if c[i]["h"] < c[i - 2]["l"]:
            out.append(("baixa", c[i]["h"], c[i - 2]["l"]))
    return out


def detect_fvg():
    c = data.candles("15m", 96)
    if not c:
        return "-"
    fv = _recent_fvgs(c)
    if not fv:
        return "Nenhum ativo"
    tipo, a, b = fv[-1]
    lo, hi = min(a, b), max(a, b)
    return f"{tipo.capitalize()} {data.fmt(lo)}–{data.fmt(hi)}"


def detect_orderblock():
    """Heurística simples: último candle de corpo dominante (>70% do range) no 15m."""
    c = data.candles("15m", 96)
    if not c:
        return "-"
    for i in range(len(c) - 1, max(1, len(c) - 60), -1):
        k = c[i]
        rng = k["h"] - k["l"]
        if rng <= 0:
            continue
        corpo = abs(k["c"] - k["o"])
        if corpo / rng > 0.7:
            lado = "Alta" if k["c"] >= k["o"] else "Baixa"
            fx1, fx2 = min(k["o"], k["c"]), max(k["o"], k["c"])
            return f"{lado} {data.fmt(fx1)}–{data.fmt(fx2)}"
    return "Nenhum claro"


def _nearest(vals, p, above=True):
    if above:
        cands = sorted(x for x in vals if x > p)
    else:
        cands = sorted((x for x in vals if x < p), reverse=True)
    return cands[0] if cands else None


def liquidity_map():
    """(BSL acima, SSL abaixo, EQH, EQL) no 15m, mais próximos do preço."""
    c = data.candles("15m", 200)
    if not c:
        return None, None, None, None
    highs, lows = _swings(c)
    p = data.price() or c[-1]["c"]
    bsl = _nearest(highs, p, above=True)
    ssl = _nearest(lows, p, above=False)

    # topos/fundos "iguais" (equal highs/lows) perto do preço
    def _eq(vs, mais_meio):
        vs = sorted(vs, reverse=mais_meio)
        for i in range(len(vs) - 1):
            if abs(vs[i] - vs[i + 1]) <= p * 0.0012:
                return (vs[i] + vs[i + 1]) / 2
        return None

    eqh = _eq([x for x in highs if x > p], True)
    eql = _eq([x for x in lows if x < p], False)
    return bsl, ssl, eqh, eql


def detect_liquidity():
    bsl, ssl, eqh, eql = liquidity_map()
    if bsl is None and ssl is None:
        return "-"
    txt = []
    if bsl is not None:
        txt.append(f"BSL {data.fmt(bsl)}")
    if ssl is not None:
        txt.append(f"SSL {data.fmt(ssl)}")
    if eqh is not None:
        txt.append("EQH perto")
    if eql is not None:
        txt.append("EQL perto")
    return " / ".join(txt)


def next_target():
    """Alvo educacional: BSL acima se viés 1h de alta; SSL abaixo se baixa."""
    c = data.candles("1h", 80)
    if not c:
        return None
    b, s, _, _ = liquidity_map()
    t = _trend(c)
    if t == "alta" and b is not None:
        return b
    if t == "baixa" and s is not None:
        return s
    if t == "lateral":
        return (max(x["h"] for x in c[-20:]) + min(x["l"] for x in c[-20:])) / 2
    return None


def alignment_score():
    """Heurística educacional: quantos timeframes apontam pro mesmo lado."""
    b4 = _trend(data.candles("4h", 40))
    b1 = _trend(data.candles("1h", 80))
    b15 = _trend(data.candles("15m", 96))
    dirs = [b4, b1, b15]
    if "alta" in dirs and "baixa" in dirs:
        return 45
    if dirs.count(dirs[0]) == 3:
        return 75
    if dirs[0] == dirs[1] or dirs[0] == dirs[2]:
        return 65
    return 55


def mkt_status():
    c = data.candles("1h", 40)
    if not c:
        return "Sem dados"
    hi = max(x["h"] for x in c[-20:])
    lo = min(x["l"] for x in c[-20:])
    meio = (hi + lo) / 2
    ult = c[-1]["c"]
    if ult > meio:
        return "Comprador ⬆️"
    if ult < meio:
        return "Vendedor ⬇️"
    return "Neutro ↔️"


def pd_state():
    """Premium/Discount na faixa de 20 candles do 1h. (texto, %da faixa)"""
    c = data.candles("1h", 40)
    if not c:
        return "Sem dados", 50
    hi = max(x["h"] for x in c[-20:])
    lo = min(x["l"] for x in c[-20:])
    if hi <= lo:
        return "Faixa estreita", 50
    pos = (c[-1]["c"] - lo) / (hi - lo) * 100
    if pos > 55:
        return f"PREMIUM (caro) {pos:.0f}%", pos
    if pos < 45:
        return f"DISCOUNT (barato) {pos:.0f}%", pos
    return f"Equilíbrio ({pos:.0f}%)", pos


def risk_alert():
    """(kind, texto): 'warn' -> st.warning | 'info' -> st.info."""
    p, _pos = pd_state()
    if p.startswith("PREMIUM") and "Alta" in detect_bias():
        return ("warn", "Preço em PREMIUM com viés alta — evite comprar caro. "
                        "Espere retrocesso pra zona (educacional, não é recomendação).")
    if p.startswith("DISCOUNT") and "Baixa" in detect_bias():
        return ("warn", "Preço em DISCOUNT com viés baixa — venda no barato é pegajoso. "
                        "Espere pullback pro premium (educacional, não é recomendação).")
    return ("info", "Nenhum alerta crítico. Painel educacional — pratique na conta demo.")


def system_logs():
    """Logs reais do painel, a partir das próprias detecções."""
    logs = []
    bos = detect_bos()
    logs.append(("✅" if bos != "Sem novo BoS" else "⏳", f"{bos}" if bos != "Sem novo BoS" else "Sem novo BoS"))
    ch = detect_choch()
    logs.append(("🔄" if ch != "Não" else "⏳", f"CHoCH: {ch}"))
    fv = detect_fvg()
    logs.append(("✅" if fv not in ("Nenhum ativo", "-") else "⏳", f"FVG: {fv}"))
    pb = detect_bias()
    logs.append(("📈" if "Alta" in pb else "📉" if "Baixa" in pb else "↔️", f"Viés 1h: {pb}"))
    ob = detect_orderblock()
    if ob not in ("Nenhum claro", "-"):
        logs.append(("📦", f"Order Block: {ob}"))
    logs.append(("🟢", "Sistema operacional — dados reais (gold-api + Binance PAXG)"))
    return logs
