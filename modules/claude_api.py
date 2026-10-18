# -*- coding: utf-8 -*-
"""Cliente de conversa —Anthropic-protocol— apontando pro hub do usuário.

Dois modos de cabeçalho:
- base_url informado (hub local): Authorization: Bearer <token>
- sem base_url (api.anthropic.com direto): x-api-key <chave>
Sem SDK, só stdlib — zero dependência.
"""
import json
import urllib.request

_URL_NUVEM = "https://api.anthropic.com/v1/messages"


def ask(api_key, model, system, history, base_url=None, timeout=120, max_tokens=700):
    """history: lista de tuplas (role, texto). role é 'user' ou 'assistant'."""
    url = (base_url.rstrip("/") + "/v1/messages") if base_url else _URL_NUVEM
    body = {
        "model": model or "auto/best-free",
        "max_tokens": max_tokens,
        "system": system,
        "messages": [
            {"role": role, "content": txt}
            for role, txt in history
            if role in ("user", "assistant")
        ],
    }
    headers = {"content-type": "application/json", "anthropic-version": "2023-06-01"}
    if base_url:
        headers["authorization"] = "Bearer " + api_key
    else:
        headers["x-api-key"] = api_key

    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        d = json.loads(resp.read().decode("utf-8"))
    partes = [b.get("text", "") for b in d.get("content", []) if b.get("type") == "text"]
    return "\n".join(partes).strip() or "(resposta vazia)"
