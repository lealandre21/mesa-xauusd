# -*- coding: utf-8 -*-
"""Cataloga os modelos do hub de IAs local (~/.claude/settings.json).

Uso:  python cataloga_hub.py
Gera: hub-modelos.md (no projeto) com os grupos: rotas, marcas e free.
Executável sempre que quiser um retrato atualizado do hub.
"""
import json
import pathlib
import urllib.request

HOME = pathlib.Path.home()
PROJ = pathlib.Path(__file__).parent
SAIDA = PROJ / "hub-modelos.md"


def pega_ids():
    cfg = json.loads((HOME / ".claude" / "settings.json").read_text(encoding="utf-8"))
    env = cfg["env"]
    base = env["ANTHROPIC_BASE_URL"].rstrip("/")
    tok = env["ANTHROPIC_AUTH_TOKEN"]
    req = urllib.request.Request(base + "/v1/models", headers={"authorization": "Bearer " + tok})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
    return [m.get("id", "") for m in data.get("data", [])], (base, tok[:8])


def monta_md(ids):
    rotas = [i for i in ids if i.startswith("auto/")]
    grupos = {"Claude (Anthropic)": "claude", "GPT (OpenAI)": "gpt-", "Gemini (Google)": "gemini",
              "Grok (xAI)": "grok", "DeepSeek": "deepseek", "GLM (Z.ai)": "glm", "Qwen (Alibaba)": "qwen"}
    bl = ["# 🛰️ Catálogo do Hub de IAs", "", f"**Total: {len(ids)} modelos.**", "",
          "## 🧠 Rotas inteligentes — as que a Mesa usa", ""]
    pro_foco = ("best", "claude", "chat", "cheap", "free", "thrifty", "reasoning", "fast")
    for r in rotas:
        if any(x in r for x in pro_foco):
            bl.append(f"- `{r}`")
    bl.append("")
    bl.append("## 👨‍👩‍👧 Marcas de peso (atalho por família)")
    bl.append("")
    for nome, chave in grupos.items():
        itens = sorted({i for i in ids if chave in i.lower()})
        if itens:
            bl.append(f"### {nome} ({len(itens)})")
            for x in itens[:12]:
                bl.append(f"- `{x}`")
            if len(itens) > 12:
                bl.append(f"- *(...e mais {len(itens) - 12})*")
            bl.append("")
    frees = sorted({i for i in ids if i.lower().endswith(":free")})
    bl.append(f"## 🆓 Modelos `:free` ({len(frees)} achados)")
    bl.append("")
    for x in frees:
        bl.append(f"- `{x}`")
    return "\n".join(bl)


if __name__ == "__main__":
    ids, (base, tokm) = pega_ids()
    SAIDA.write_text(monta_md(ids), encoding="utf-8")
    print(f"[ok] {len(ids)} modelos · base {base} · token {tokm}...")
    print(f"[ok] catálogo salvo em {SAIDA}")
