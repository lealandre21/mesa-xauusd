# -*- coding: utf-8 -*-
"""CONSULTOR-1: o robozinho conselheiro da Mesa.

Troca de dica a cada 45s, com dicas geradas a partir dos dados reais
(sessão, faixa, liquidez) + dicas de cuidado (respiração, gestão).
Educacional — nunca recomenda ordem.
"""
import time

import streamlit as st

from modules import dashboard, smc


def _dicas():
    sess = dashboard.current_session()
    pd_txt, _pos = smc.pd_state()
    liq = smc.detect_liquidity()
    fora = ("Fora" in sess) or ("Transição" in sess)
    return [
        (
            f"Sessão: {sess}. "
            + (
                "Sem killzone ativa — melhor treinar leitura do que clicar. 🧘"
                if fora
                else "Killzone ligada — foque, mas só com confirmação."
            )
        ),
        f"Faixa atual: {pd_txt}. Premium = caro (comprar aqui é pagar topo). Discount = barato (vender aqui é pegar fundo).",
        f"Liquidez: {liq}. O preço adora visitar onde o stop todo o mundo mora — espere a varrida, depois a decisão.",
        "🫁 Pausa calma: inspira 4s, segura 4s, solta 6s. O mercado não tem hora de fechar — cuidar da cabeça também é gestão de risco.",
        "🛡️ Regra de ouro: risco ≤ 1% por trade e R:R mínimo 1:2. Setup ruim = DE FORA — de fora não perde dinheiro.",
        "📚 Tudo aqui é estudo e prática em conta demo, sempre. Nenhum número aqui é recomendação.",
        "👀 Dica de leitura: pavio não é rompimento. Só corpo fechando rompendo ou BoS de verdade.",
        "🧠 Faixa premium + sem BoS = festa de ninguém. Paciência é uma posição válida.",
    ]


def render():
    dicas = _dicas()
    idx = int(time.time() // 45) % len(dicas)
    tip = dicas[idx]
    html = f"""
    <div style="display:flex;align-items:center;gap:14px;margin:4px 0 12px 0;">
      <div
        style="font-size:44px;filter(drop-shadow(0 4px 8px rgba(0,0,0,.4)));"
      >🤖</div>
      <div style="background:rgba(246,199,68,.10);border:1px solid rgba(246,199,68,.35);
                  border-radius:14px;padding:10px 16px;color:#f6c744;">
        <b>CONSULTOR-1:</b> {tip}
      </div>
    </div>
    <style>
      @keyframes flutuador {{
        0%   {{ transform: translateY(0) rotate(-3deg); }}
        50%  {{ transform: translateY(-9px) rotate(3deg); }}
        100% {{ transform: translateY(0) rotate(-3deg); }}
      }}
      @keyframes piscar {{
        0%, 88%, 100% {{ opacity: 1; }}
        92% {{ opacity: .4; }}
      }}
      div[style*="font-size:44px" i] {{ animation: flutuador 3s ease-in-out infinite; }}
    </style>
    """
    st.markdown(html, unsafe_allow_html=True)
