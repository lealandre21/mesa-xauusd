# -*- coding: utf-8 -*-
"""🎬 Biblioteca de vídeos de estudo (Shorts do YouTube).

- Conceito detectado no plano → chip com busca de Shorts sobre o tema.
- O Leala pode FIXAR o próprio vídeo favorito por conceito (cola a URL
  numa caixinha) → fica salvo em videos_fixados.json e passa a ser o
  vídeo padrao mostrado. Biblioteca dele, escolha dele.
Nunca embutimos vídeo da a gente embaixo — só link pra YouTube (respeita
os criadores; o app continua leve).
"""
import json
import os
import urllib.parse

ARQ_FIXADOS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "videos_fixados.json")

# conceito → (nome amigável, termo de busca no YouTube)
CONCEITOS = {
    "bos": ("Break of Structure (continua o fluxo)",
            "SMC break of structure ouro shorts"),
    "choch": ("CHoCH (mudança de fluxo)",
              "SMC CHoCH change of character shorts"),
    "fvg": ("FVG / Imbalance (o vão que o preço costuma voltar)",
            "ICT fair value gap FVG shorts"),
    "liquidez": ("Liquidez: BSL/SSL e INDUCEMENT (o vilão)",
                 "ICT liquidity sweep inducement shorts"),
    "ote": ("Fibonacci OTE (0.62–0.79)", "ICT optimal trade entry fibonacci shorts"),
    "pd": ("Premium & Discount (metade cara / metade barata)",
           "ICT premium discount zones shorts"),
    "setup": ("Entrada: gatilho de corpo + plano", "SMC entry setup confirmation shorts"),
}

# termos que ligam cada conceito nos textos do plano
TERMOS = {
    "bos": ("bos", "break", "quebra"),
    "choch": ("choch", "character"),
    "fvg": ("fvg", "gap", "imbalance"),
    "liquidez": ("liquidez", "inducement", "sweep", "stop hunt", "eqh", "eql"),
    "ote": ("ote", "fibo", "fibonacci", "0.6", "0.7"),
    "pd": ("premium", "discount", "equilíbrio"),
    "setup": ("gatilho", "corpo", "confir"),
}


def conceitos_do_plano(p: dict) -> list[str]:
    """Conceitos citados em headline/gatilho/invalidação (ordem de pureza)."""
    texto = " ".join(str(p.get(k, "")) for k in ("headline", "gatilho", "invalidacao")).lower()
    out = []
    for chave, termos in TERMOS.items():
        if any(t in texto for t in termos):
            out.append(chave)
    return out or ["setup"]


def busca_url(termo: str) -> str:
    return "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(termo)


def id_de(url: str) -> str | None:
    """Extrai o ID do vídeo de vários formatos de link do YouTube."""
    u = (url or "").split("?")[0].rstrip("/")
    for marcador in ("/shorts/", "youtu.be/", "/embed/", "watch/"):
        if marcador in u:
            return u.split(marcador)[-1] or None
    if "watch?v=" in url:
        return url.split("watch?v=")[-1].split("&")[0] or None
    return None


def embed_url(url: str) -> str | None:
    """Link → URL de player embutido (iframe) ou None se id não sair."""
    vid = id_de(url)
    return f"https://www.youtube.com/embed/{vid}" if vid else None


def fixados() -> dict:
    """URLs fixadas pelo usuário: {conceito: url}."""
    try:
        with open(ARQ_FIXADOS, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def fixar(conceito: str, url: str) -> bool:
    """Salva vídeo favorito do conceito. False se url estranha."""
    u = (url or "").strip()
    if not u.startswith(("http://", "https://")) or conceito not in CONCEITOS:
        return False
    dados = fixados()
    dados[conceito] = u
    with open(ARQ_FIXADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
    return True


def video_do_conceito(conceito: str) -> tuple[str, str]:
    """(rótulo, url) pro chip — favorito fixado ou busca do conceito."""
    nome, termo = CONCEITOS.get(conceito, CONCEITOS["setup"])
    u = fixados().get(conceito)
    if u:
        return f"🎬 Seu vídeo: {nome}", u
    return f"🎬 60s sobre: {nome}", busca_url(termo)
