# -*- coding: utf-8 -*-
"""Plano do momento + dicionário visual das zonas SMC.

O plano responde em 3 perguntas: pra onde? (4h→1h) · onde esperar? (zona)
· qual gatilho? (corpo 15m fechando). Educational: é roteiro de estudo,
não sinal.
"""
from modules import data, smc


def plano():
    """Dict: direção por timeframe, checks, gatilho, alvo, invalidação."""
    t4 = smc._trend(data.candles("4h", 40))
    t1 = smc._trend(data.candles("1h", 80))
    t15 = smc._trend(data.candles("15m", 96))
    pd_txt, pos = smc.pd_state()
    fv = smc.detect_fvg()
    tem_fvg = fv not in ("Nenhum ativo", "-")
    bos = smc.detect_bos()

    checks = [
        (f"4h: fluxo de {t4}", t4 in ("alta", "baixa")),
        (f"1h: fluxo de {t1}", t1 in ("alta", "baixa")),
        (f"15m: gatilho possível em {t15}", t15 != "lateral" or tem_fvg),
        (f"Preço: {pd_txt}", 45 <= pos <= 55 or t1 in ("alta", "baixa")),
        (f"BoS: {bos}", bos != "Sem novo BoS"),
    ]

    if t4 == t1 == t15 == "alta" and pos < 55:
        headline = "COMPRA EM RETROCESSO (plan A)"
        gatilho = "Espere o toque no FVG/zona + candle 15m fechando (corpo) pra cima."
        alvo, inval = smc.next_target(), "fechamento 15m abaixo do fundo da zona"
    elif t4 == t1 == t15 == "baixa" and pos > 45:
        headline = "VENDA EM PULLBACK (plan A invertido)"
        gatilho = "Toco no FVG/zona de baixa + candle 15m fechando (corpo) pra baixo."
        alvo, inval = smc.next_target(), "fechamento 15m acima do topo da zona"
    elif (t4 == t1 == t15) and t4 != "lateral":
        headline = f"ALINHADO {t4} — esperar ponto chave (preço {pd_txt.split()[0]})"
        gatilho = "Entrada só quando preço voltar pra zona (discount/premium) com corpo 15m confirmando."
        alvo, inval = smc.next_target(), "fluxo 1h inverter (CHoCH)"
    elif t4 == t1 and t4 != "lateral":
        headline = f"FLUXO DE {t4.upper()} (4h+1h) — AGUARDAR GATILHO 15m"
        gatilho = "Esperar o 15m virar pro mesmo lado OU zona (FVG/OB/liquidez) tocar: corpo 15m fecha confirmando."
        alvo, inval = smc.next_target(), "CHoCH no 1h (fluxo perde força)"
    else:
        headline = "SEM ALINHAMENTO — DE FORA"
        gatilho = "Nenhum. Esperar 4h/1h alinhar OU zona de liquidez clara tocar."
        alvo, inval = smc.next_target(), "CHoCH em 1h consolidando"

    return {
        "headline": headline,
        "checks": checks,
        "gatilho": gatilho,
        "alvo": alvo,
        "invalidacao": inval,
        "trends": (t4, t1, t15),
    }


# ---------------------------------------------------------------
# cards explicativos: (nome, o que é, o que esperar, gatilho, invalidação)
# ---------------------------------------------------------------

def zonas_explicadas():
    fv = smc.detect_fvg()
    ob = smc.detect_orderblock()
    bsl, ssl, eqh, eql = smc.liquidity_map()
    cards = [
        {
            "nome": "🕳️ FVG / Imbalance",
            "status": fv,
            "o_que_e": "Buraco no preço: candle 1 e 3 não se encostam. O mercado subiu/desceu \"rápido demais\".",
            "esperar": "Preço voltar pro buraco (retrocesso) e REAGIR dentro dele.",
            "gatilho": "Vela 15m fecha (corpo) na direção do fluxo DENTRO da zona.",
            "invalida": "Fechar inteiro do outro lado do gap (virou filtro 3-fracos).",
        },
        {
            "nome": "📦 Order Block",
            "status": ob,
            "o_que_e": "Última vela \"contrária\" (corpo dominante) antes do impulso. Ali ficaram ordens institucionais.",
            "esperar": "Mitigação: o preço re-testar a zona do corpo e respeitar (desenho de rejeição).",
            "gatilho": "Pavio toca a borda + corpo fecha longe, na direção do fluxo 1h.",
            "invalida": "Corpo fechando ATRÁS de toda a zona (OB quebrou/morreu).",
        },
        {
            "nome": "🪤 Liquidez (BSL/SSL/EQH/EQL)",
            "status": f"BSL {data.fmt(bsl)} · SSL {data.fmt(ssl)}"
            if bsl and ssl
            else "-",
            "o_que_e": "Pools de stops acima de topos (BSL) e abaixo de fundos (SSL). Topos/fundos ''iguais'' = magnetizer (EQH/EQL).",
            "esperar": "Varredura: pavio atravessa o nível, MIRA VOCÊ (stop hunt), mas não SUSTENTA.",
            "gatilho": "Pavio saca a liquidez + candle fecha de volta do lado original.",
            "invalida": "Corpo fecha além do nível E mantém — a varrida virou rompimento real.",
        },
        {
            "nome": "⚖️ Premium / Discount",
            "status": smc.pd_state()[0],
            "o_que_e": "Metade de cima da faixa = caro (premium). Metade de baixo = barato (discount). 50% = equilíbrio.",
            "esperar": "Comprar só em discount / vender só em premium, cumprindo fluxo do HTF.",
            "gatilho": "Preço em discount + gatilho de alta (FVG/OB batendo) = mesmo plano alinhado.",
            "invalida": "Faixa sendo respeitada ao contrário: preço gruda no topo/subestima fundo novo.",
        },
    ]
    return cards


def bar_faixa():
    """SVG: régua premium→discount com marcador do preço atual."""
    _txt, pos = smc.pd_state()
    try:
        pos = max(0, min(100, float(pos)))
    except (TypeError, ValueError):
        pos = 50
    x = pos  # percent
    return f"""
<div style="margin:2px 0 0 2px;">
<svg viewBox="0 0 300 54" style="width:100%;height:auto;">
  <defs>
    <linearGradient id="gfx" x1="0" x2="1">
      <stop offset="0%" stop-color="#26a69a"/>
      <stop offset="50%" stop-color="#8893aa"/>
      <stop offset="100%" stop-color="#ef5350"/>
    </linearGradient>
  </defs>
  <rect x="10" y="18" width="280" height="14" rx="7" fill="url(#gfx)" opacity="0.85"/>
  <text x="10" y="12" font-size="10" fill="#5c646e">0% discount (barato)</text>
  <text x="290" y="12" font-size="10" fill="#5c646e" text-anchor="end">100% premium (caro)</text>
  <text x="150" y="46" font-size="10" fill="#8893aa" text-anchor="middle">50% equilíbrio · preço: {x:.0f}%</text>
  <line x1="{10 + x / 100 * 280}" y1="14" x2="{10 + x / 100 * 280}" y2="36" stroke="#f6c744" stroke-width="3"/>
  <circle cx="{10 + x / 100 * 280}" cy="25" r="4" fill="#f6c744"/>
</svg>
</div>
"""
