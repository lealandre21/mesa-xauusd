# -*- coding: utf-8 -*-
"""Gráfico da Mesa: velas reais (Binance PAXG) com zonas SMC marcadas.

- FVG: faixas translúcidas (verde = alta, vermelho = baixa)
- Order Block: retângulo roxo no último candle de corpo dominante
- BSL/SSL: linhas pontilhadas (mapa de liquidez do 15m)
- 50%: equilíbrio da faixa de 20 candles
Leitura educacional — nada disso é sinal de ordem.
"""
from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

from modules import data, smc


def _build(interval: str = "1h", limit: int = 120, height: int = 540) -> go.Figure:
    c = data.candles(interval, limit)
    tempo = [datetime.fromtimestamp(k["t"] / 1000) for k in c]

    fig = go.Figure(
        go.Candlestick(
            x=tempo,
            open=[k["o"] for k in c],
            high=[k["h"] for k in c],
            low=[k["l"] for k in c],
            close=[k["c"] for k in c],
            name="PAXG (proxy XAUUSD)",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
            increasing_fillcolor="rgba(38,166,154,.7)",
            decreasing_fillcolor="rgba(239,83,80,.7)",
        )
    )

    # --- FVGs recentes ---
    for tipo, a, b in smc._recent_fvgs(c)[-3:]:
        lo, hi = min(a, b), max(a, b)
        cor = "rgba(38,166,154,.16)" if tipo == "alta" else "rgba(239,83,80,.16)"
        fig.add_hrect(
            y0=lo, y1=hi,
            fillcolor=cor, line_width=0,
            annotation_text=f"FVG {tipo}",
            annotation_font_size=9,
        )

    # --- último Order Block (corpo dominante) ---
    for i in range(len(c) - 1, max(1, len(c) - 60), -1):
        k = c[i]
        rng = k["h"] - k["l"]
        if rng <= 0:
            continue
        corpo = abs(k["c"] - k["o"])
        if corpo / rng > 0.7:
            y0, y1 = min(k["o"], k["c"]), max(k["o"], k["c"])
            fig.add_shape(
                type="rect",
                x0=tempo[i], x1=tempo[-1],
                y0=y0, y1=y1,
                fillcolor="rgba(155,109,255,.20)",
                line=dict(color="rgba(155,109,255,.6)", dash="dot"),
            )
            fig.add_annotation(
                x=tempo[i], y=(y0 + y1) / 2,
                text="OB", showarrow=False, font=dict(size=9, color="#9b6dff"),
                xanchor="right",
            )
            break

    # --- liquidez 15m ---
    bsl, ssl, eqh, eql = smc.liquidity_map()
    for nivel, nome in [(bsl, "BSL"), (ssl, "SSL")]:
        if nivel is not None:
            fig.add_hline(
                y=nivel, line_dash="dot", line_color="#f6c744", line_width=1,
                annotation_text=nome,
                annotation_position="right",
                annotation_font_size=9,
                annotation_font_color="#f6c744",
            )

    # --- equilíbrio 50% ---
    if c:
        hi = max(x["h"] for x in c[-20:])
        lo = min(x["l"] for x in c[-20:])
        meio = (hi + lo) / 2
        fig.add_hline(
            y=meio, line_dash="dash", line_color="#8893aa", line_width=1,
            annotation_text="50%",
            annotation_position="top left",
            annotation_font_size=9,
            annotation_font_color="#8893aa",
        )
        # preço vivo na lateral direita (rótulo curto pra não colidir)
        fig.add_hline(
            y=c[-1]["c"], line_color="#26a69a", line_width=1,
            annotation_text=f"↑ {data.fmt(c[-1]['c'])}",
            annotation_position="right",
            annotation_font_size=9,
            annotation_font_color="#26a69a",
        )

    fig.update_layout(
        title=dict(text=f"XAUUSD · {interval}", x=0.01, xanchor="left"),
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#5c646e", size=11),
        showlegend=False,
        yaxis=dict(side="right", showgrid=False, tickformat=",.0f"),
        xaxis=dict(showgrid=False),
    )
    return fig


def show_chart(interval: str = "1h", height: int = 540):
    try:
        fig = _build(interval, height=height)
    except Exception as e:
        st.warning(f"Gráfico indisponível agora: {e}")
        return
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False},
    )
