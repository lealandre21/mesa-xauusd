# -*- coding: utf-8 -*-
"""Voz da mesa: transforma o PLANO DO MOMENTO em áudio (MP3) pra ouvir.

- edge-tts (Microsoft neural) é gratuito e online
- Voz: pt-BR-AntonioNeural (masculina, calma)
- `src()` monta o roteiro da leitura; `gerar()` devolve bytes de MP3
-.cache por hash do texto: mesma leitura não re-sintetiza a cada F5
"""
import asyncio
import hashlib

import edge_tts
import streamlit as st

_VOZ = "pt-BR-AntonioNeural"


def src() -> str:
    """Roteiro narrado (~20s) com os dados do momento."""
    from modules import data, dashboard, plan

    p = plan.plano()
    preco = data.price()
    aberto, quando_fx = dashboard.mercado_fx()
    quando_txt = "mercado aberto" if aberto else f"mercado fechado — {quando_fx}"
    alvo = f"{data.fmt(p['alvo'])} dólares" if p["alvo"] else "sem alvo definido"
    return (
        f"Mesa XAUUSD. {dashboard.hora_brt().strftime('%H horas e %M minutos')}. "
        f"{quando_txt}. "
        f"Preço do ouro — proxy PAXG: {data.fmt(preco) if preco else 'sem dado'} dólares. "
        f"Plano do momento: {p['headline'].replace(' — ', '. ')}. "
        f"Gatilho a observar: {p['gatilho']}. "
        f"Alvo pela estrutura: {alvo}. Invalidação: {p['invalidacao']}. "
        "Lembrete educacional: nada aqui é recomendação — treine na conta demo."
    )


@st.cache_data(show_spinner=False)
def gerar(texto: str) -> bytes | None:
    """Sintetiza MP3 do texto (cache por conteúdo). None se falhar."""
    chunks: list[bytes] = []

    async def _coletar():
        comunicante = edge_tts.Communicate(texto, _VOZ)
        async for chunk in comunicante.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])

    try:
        asyncio.run(_coletar())
        return b"".join(chunks) or None
    except Exception:
        return None


def chave(texto: str) -> str:
    """Hash curto do texto (pra UI mostrar tamanho do áudio)."""
    return hashlib.sha1(texto.encode("utf-8")).hexdigest()[:8]
