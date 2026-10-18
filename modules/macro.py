# -*- coding: utf-8 -*-
"""Sessões e calendário — horário de Brasília (UTC-3), currículo de estudo:
Ásia 21h–1h | LOKZ 3h–6h | NYOKZ 8h–11h | LCKZ 11h–13h.
"""
from datetime import datetime, timedelta, timezone

_BRT = timezone(timedelta(hours=-3))

KILLZONES = {
    "Ásia": ((21, 24), (0, 1)),
    "London Open (LOKZ)": ((3, 6),),
    "New York Open (NYOKZ)": ((8, 11),),
    "London Close (LCKZ)": ((11, 13),),
}


def _agora():
    return datetime.now(_BRT)

def _dentro(h, janela):
    ini, fim = janela
    if ini <= fim:
        return ini <= h < fim
    return h >= ini or h < fim


def _status(k):
    h = _agora().hour
    for janelas in KILLZONES[k]:
        if _dentro(h, janela):
            return "✅ Aberta"
    return "⏳ Fechada"


def asia_session():
    return _status("Ásia")


def london_session():
    return _status("London Open (LOKZ)")


def newyork_session():
    return _status("New York Open (NYOKZ)")


def next_news():
    # Placeholder — depois a gente pluga um feed de calendário econômico.
    return [
        {"evento": "USD CPI", "impacto": "🔴 Alto", "tempo": "verificar calendário"},
        {"evento": "Unemployment Claims", "impacto": "🟡 Médio", "tempo": "verificar calendário"},
        {"evento": "FOMC", "impacto": "🔴 Alto", "tempo": "verificar calendário"},
    ]
