# -*- coding: utf-8 -*-
"""Manchetes de forex via RSS gratuito (sem chave de API).

- ForexLive / FXStreet / Investing (mercado em geral + commodities)
- Parse com xml.etree (biblioteca padrão) — zero dependência nova
- Cache 5 min pra não martelar o servidor
- Conteúdo informativo: manchete NÃO é análise nem recomendação.
"""
import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

import streamlit as st

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

FONTES = [
    ("ForexLive", "https://www.forexlive.com/feed/news"),
    ("FXStreet", "https://www.fxstreet.com/rss/news"),
    ("Investing", "https://www.investing.com/rss/news_25.rss"),
]

MAX_TOTAL = 14


def _limpa(texto: str, limite: int = 150) -> str:
    """Tira tags HTML de sobra e corta com linha tranquila."""
    t = re.sub(r"<[^>]+>", " ", html.unescape(texto or ""))
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) > limite:
        t = t[: limite - 1].rstrip() + "…"
    return t


@st.cache_data(ttl=300, show_spinner=False)
def manchetes():
    """Lista consolidada de manchetes reais → [{fonte, titulo, link, quando(BRT)}]."""
    itens = []
    hoje = datetime.now(timezone.utc)
    req_ontem = hoje - timedelta(hours=72)
    for nome, url in FONTES:
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                raiz = ET.fromstring(r.read())
            canal = raiz.find("channel")
            if canal is None:
                # Atom (feed com <entry> na raiz) → adapta
                entries = raiz.findall("{http://www.w3.org/2005/Atom}entry")[:8]
                for e in entries:
                    titulo = _limpa(e.findtext("{http://www.w3.org/2005/Atom}title", ""))
                    link_el = e.find("{http://www.w3.org/2005/Atom}link")
                    link = (link_el.get("href") if link_el is not None else "") or ""
                    data_txt = e.findtext("{http://www.w3.org/2005/Atom}updated", "")
                    itens.append(_item(nome, titulo, link, data_txt, req_ontem))
                continue
            for e in canal.findall("item")[:8]:
                titulo = _limpa(e.findtext("title", ""))
                link = (e.findtext("link") or "").strip()
                data_txt = (e.findtext("pubDate") or "").strip()
                itens.append(_item(nome, titulo, link, data_txt, req_ontem))
        except Exception:
            continue  # fonte fora? a mesa mostra as outras, sem drama
    # ordena por data BRT (mais nova primeira) e limita
    itens = [i for i in itens if i]
    itens.sort(key=lambda x: x["quando"], reverse=True)
    return itens[:MAX_TOTAL]


def _quando(data_txt):
    """Parse da data com plano B: RFC822 → ISO sem fuso (assumindo UTC)."""
    if not data_txt:
        return None
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(data_txt.strip())
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(data_txt.strip())
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        except (TypeError, ValueError):
            return None


def _item(nome, titulo, link, data_txt, limite_dt):
    if not titulo:
        return None
    dt = _quando(data_txt)
    if dt is None or dt < limite_dt:
        return None  # sem data legível ou velha demais, fora
    return {
        "fonte": nome,
        "titulo": titulo,
        "link": link,
        "quando": dt.astimezone(timezone(timedelta(hours=-3))),
    }


# ------ Faixa rolando (ticker) ---------------------------------------------

_CSS = """
<style>
.mesa-ticker{width:100%;overflow:hidden;position:relative;
  border:1px solid rgba(250,250,250,.18);border-radius:8px;
  background:rgba(250,250,250,.04);padding:6px 0;height:38px}
.mesa-trilho{display:inline-block;white-space:nowrap;
  animation:mesa-roll 90s linear infinite;padding-left:12px}
.mesa-trilho:hover{animation-play-state:paused}
@keyframes mesa-roll{from{transform:translateX(0)}to{transform:translateX(-50%)}}
.mesa-item{margin-right:34px;font-size:13px;color:rgba(250,250,250,.85)}
.mesa-fonte{font-weight:700;color:#f0b90b;margin-right:6px}
</style>
"""

def banda_html(itens) -> str:
    """HTML do ticker: conteúdo duplicado pra rolar em loop sem lacuna."""
    meio = "".join(
        f'<span class="mesa-item">'
        f'<span class="mesa-fonte">[{i["fonte"]}]</span>{html.escape(i["titulo"])}</span>'
        for i in itens
    )
    return f"""{_CSS}
<div class="mesa-ticker"><div class="mesa-trilho">{meio}{meio}</div></div>"""


def banda(itens):
    st.markdown(banda_html(itens), unsafe_allow_html=True)


def lista(itens, limite=6):
    """Lista compacta das últimas manchetes (com link clicável)."""
    for i in itens[:limite]:
        st.markdown(
            f"`{i['quando'].strftime('%H:%M')}` **{i['fonte']}** — "
            f"[{i['titulo']}]({i['link']})"
        )
    st.caption("⚠️ Manchete é informação, não leitura de preço. A análise é da Mesa (SMC/ICT).")
