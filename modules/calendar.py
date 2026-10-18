# -*- coding: utf-8 -*-
"""Calendário econômico real (Forex Factory, feed público sem chave).
Foco XAUUSD: eventos USD/All com impacto Alto/Médio. Datas em Brasília.
"""
import json
import urllib.request
from datetime import datetime, timedelta, timezone

import streamlit as st

_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
_BRT = timezone(timedelta(hours=-3))

_IMP = {
    "High": "🔴 Alto",
    "Medium": "🟡 Médio",
    "Low": "🟢 Baixo",
    "Holiday": "🌴 Feriado",
}


@st.cache_data(ttl=1800, show_spinner=False)
def _fetch():
    try:
        req = urllib.request.Request(_URL, headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return []


def upcoming(somente_relevantes=True):
    """Próximos eventos (BRT), mais relevantes primeiro."""
    agora = datetime.now(_BRT)
    rows = []
    for e in _fetch():
        try:
            dt = datetime.fromisoformat(e["date"]).astimezone(_BRT)
        except (KeyError, ValueError, TypeError):
            continue
        if dt < agora:
            continue
        pais = e.get("country", "-")
        imp = e.get("impact", "Low")
        if somente_relevantes and not (pais in ("USD", "All") and imp in ("High", "Medium")):
            continue
        rows.append(
            {
                "Quando": dt.strftime("%d/%m %H:%M"),
                "Evento": str(e.get("title", "")),
                "Moeda": pais,
                "Impacto": _IMP.get(imp, imp),
            }
        )
    rows.sort(key=lambda r: r["Quando"])
    return rows[:14]


def show_calendar(somente_relevantes=True):
    rows = upcoming(somente_relevantes)
    if not rows:
        st.info("Nenhum evento na janela escolhida. (Atualiza a cada 30 min)")
        return
    st.table(rows)
    st.caption(
        "Fonte: Forex Factory (feed público) · datas convertidas pra Brasília · "
        "🔴 Alto costuma mover o XAUUSD — vento forte derruba triz. "
        "Painel educacional."
    )
