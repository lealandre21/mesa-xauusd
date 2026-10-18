# -*- coding: utf-8 -*-
"""Fibo de estudo: último impulso real → OTE (0.62–0.79) e extensão.

Regras do currículo (cap. 9): fibo precisa de LÓGICA por trás — por isso
só desenha depois de achar a perna de impulso completa (fundo antes do topo
= perna de alta; topo antes do fundo = perna de baixa). Níveis principais
apenas: 0.50 (meio), OTE 0.62/0.705/0.79 e extensão -0.272/-0.618.
Educacional — nunca sinal sozinho.
"""
from modules import data


def perna(tf: str = "15m", n: int = 96):
    """Última perna de impulso no timeframe → dict ou None (dados curtos)."""
    c = data.candles(tf, n)
    if not c or len(c) < 40:
        return None

    topo = max(c, key=lambda k: k["h"])
    fundo = min(c, key=lambda k: k["l"])
    i_topo = c.index(topo)
    i_fundo = c.index(fundo)

    direcao = "alta" if i_fundo < i_topo else "baixa"
    L, H = fundo["l"], topo["h"]
    span = H - L
    if span <= 0:
        return None

    if direcao == "alta":
        # retração medida DO TOPO pra baixo: 0.62 fica mais perto do topo
        def lv(r):
            return H - span * r
        ext_alvo = L - span * 0.272       # expansão além do fundo(-0.272)
        ext_alvo2 = L - span * 0.618
    else:
        # perna de baixa: retração DO FUNDO pra cima
        def lv(r):
            return L + span * r
        ext_alvo = H + span * 0.272
        ext_alvo2 = H + span * 0.618

    n62, n70, n79 = lv(0.62), lv(0.705), lv(0.79)
    n50 = lv(0.50)

    ote_lo, ote_hi = (n79, n62) if direcao == "alta" else (n62, n79)
    preco = data.price() or c[-1]["c"]

    def _ordem(p):
        """Posição do preço na retração em fração 0..1 (0=início da perna)."""
        return (p - L) / span if direcao == "alta" else (H - p) / span

    r_preco = _ordem(preco)
    if direcao == "alta":
        dentro = ote_hi >= preco >= ote_lo
    else:
        dentro = ote_lo <= preco <= ote_hi

    if dentro:
        estado = f"DENTRO do OTE (retração {r_preco:.0%}) — zona de interesse"
    elif r_preco < 0.62:
        estado = f"retração rasa ({r_preco:.0%}) — mercado ainda não veio ao OTE"
    elif r_preco < 0.79:
        estado = f"fundo do OTE ({r_preco:.0%}) — perto da invalidação do fundo"
    else:
        estado = f"fugiu da zona ({r_preco:.0%}) — perna pode estar invalidated/adormecida"

    return {
        "direcao": direcao, "tf": tf, "preco": preco,
        "L": L, "H": H, "span": span,
        "n50": n50, "n62": n62, "n70": n70, "n79": n79,
        "ext_alvo": ext_alvo, "ext_alvo2": ext_alvo2,
        "ote": (ote_lo, ote_hi),
        "r_preco": r_preco, "estado": estado,
    }


def linha(f=None):
    """1 linha de caption com o núcleo do OTE (pra UI compacta)."""
    f = f or perna()
    if not f:
        return "📐 Fibo: sem perna clara no 15m — paciência."
    lo, hi = f["ote"]
    return (f"📐 Fibo 15m: impulso de {f['direcao']} {data.fmt(f['L'])}→{data.fmt(f['H'])} · "
            f"OTE {data.fmt(lo)}–{data.fmt(hi)} · **{f['estado']}**")


def niveis(f=None):
    """[(nome, preço)] pros pontos principais, do fundo pro topo."""
    f = f or perna()
    if not f:
        return []
    if f["direcao"] == "alta":
        return [
            ("ext -0.618 (alvo distante)", f["ext_alvo2"]),
            ("ext -0.272 (alvo fibo)", f["ext_alvo"]),
            ("fundo da perna (L)", f["L"]),
            ("0.79 (OTE fundo)", f["n79"]),
            ("0.705 (O sweet spot)", f["n70"]),
            ("0.62 (OTE topo)", f["n62"]),
            ("0.50 (meio)", f["n50"]),
            ("topo da perna (H)", f["H"]),
        ]
    return [
        ("ext +0.618 (alvo distante)", f["ext_alvo2"]),
        ("ext +0.272 (alvo fibo)", f["ext_alvo"]),
        ("topo da perna (H)", f["H"]),
        ("0.79 (OTE topo)", f["n79"]),
        ("0.705 (sweet spot)", f["n70"]),
        ("0.62 (OTE fundo)", f["n62"]),
        ("0.50 (meio)", f["n50"]),
        ("fundo da perna (L)", f["L"]),
    ]
