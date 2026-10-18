# -*- coding: utf-8 -*-
"""Detecção automática do hub local de IAs.

O Leala já usa um roteador local de IAs (configurado pelo Claude Code em
~/.claude/settings.json: ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN).
A Mesa reaproveita ESE gateway — sem colar chave nenhuma.

Aqui o token nunca é impresso inteiro: só versão mascarada.
"""
import json
import pathlib

_SETTINGS = pathlib.Path.home() / ".claude" / "settings.json"


def gateway():
    """Devolve {base_url, token, model} se o hub estiver configurado, senão None."""
    try:
        cfg = json.loads(_SETTINGS.read_text(encoding="utf-8"))
        env = cfg.get("env", {})
        base = (env.get("ANTHROPIC_BASE_URL") or "").rstrip("/")
        token = (env.get("ANTHROPIC_AUTH_TOKEN") or "").strip()
        model = (cfg.get("model") or "auto/best-free").strip()
        if base and token:
            return {"base_url": base, "token": token, "model": model}
    except Exception:
        pass
    return None


def mascarado_cfg(cfg=None):
    """Token curto pra exibir na UI (ex.: 'sk-9737ed…8045')."""
    cfg = cfg or gateway()
    if not cfg:
        return "—"
    t = cfg["token"]
    return (t[:8] + "…" + t[-4:]) if len(t) > 16 else " Tok oculto "
