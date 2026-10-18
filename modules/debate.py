# -*- coding: utf-8 -*-
"""Debate MULTI-IA: duas IAs DIFERENTES do hub discutem o mesmo gráfico.

- CLAUDE-Estrutura: rota Claude (leitura de estrutura, viés, zonas).
- QUANT-Fluxo: modelo free de 120B (números, ceticismo com narrativa).
Modelos de "cérebros" diferentes = desacordo real, não encenado.

Fluxo (4 chamadas por rodada):
1) A abre o caso
2) B rebate (já lendo a fala de A)
3) A responde a réplica
4) Moderador (Claude) dá o veredicto

Educacional: ninguém recomenda ordem; conta demo sempre.
"""
from modules import claude_api, secrets

_LUTADOR_A = (
    "🤖 CLAUDE-Estrutura",
    ["auto/claude-haiku", "auto/best-chat"],
    "Priorize ESTRUTURA: viés de TFs superiores, BoS/CHoCH por corpo, "
    "premium/discount, zonas FVG/OB e mapa de liquidez. Defenda a leitura "
    "estrutural usando os números do contexto.",
)
_LUTADOR_B = (
    "🧪 QUANT-Fluxo",
    ["openrouter/nvidia/nemotron-3-super-120b-a12b:free", "auto/best-free", "auto/thrifty"],
    "Priorize NÚMEROS e ceticismo: alinhamento dos TFs, posição na faixa "
    "premium/discount, R:R objetivo, tamanho da amostra. ATACUE a narrativa "
    "estruturalista quando faltar estatística; exija gatilho objetivo.",
)

_MODEL_MOD = "auto/claude-haiku"

_BASE_SYS = (
    "Você é {nome}, analista de uma mesa de ESTUDO (SMC/ICT) sobre XAUUSD, "
    "em PT-BR. Você está em DEBATE com {outro}. Postura: {postura}\n\n"
    "REGRAS:\n"
    "- Use SOMENTE o CONTEXTO DO MERCADO fornecido; não invente números.\n"
    "- Máximo 5 linhas, direto.\n"
    "- Não recomende ordem; lembre conta demo com naturalidade."
)

_SYS_MOD = (
    "Você é o MODERADOR da MESA XAUUSD (estudo SMC/ICT, PT-BR). Recebeu o "
    "debate entre a IA Estrutura e a IA Quant. Dê o VEREDICTO em no máximo "
    "4 linhas: quem tem razão nos pontos, onde ambos concordam, e qual "
    "gatilho objetivo observar (com números do contexto). Não recomende "
    "ordem; lembre conta demo.\n\n"
    "CONTEXTO DO MERCADO:\n{ctx}\n\nDEBATE:\n{debate}"
)


def _pedir(gw, modelo, system, pergunta, timeout=120):
    """Uma chamada. Exceção sobe pro chamador (esquema de fallback)."""
    return claude_api.ask(
        gw["token"], modelo, system,
        [("user", pergunta)],
        base_url=gw["base_url"],
        timeout=timeout,
        max_tokens=1400,
    ).strip()


def rodar(pergunta: str) -> list:
    """Devolve lista de blocos markdown: pergunta, falas, réplica e veredicto."""
    gw = secrets.gateway()
    if not gw:
        return ["⚠️ Sem hub de IAs detectado — confira ~/.claude/settings.json."]

    ctx = contexto_curto()
    nome_a, rotas_a, postura_a = _LUTADOR_A
    nome_b, rotas_b, postura_b = _LUTADOR_B

    blocos = [f"🎯 **Pergunta do debate:** {pergunta}", ""]

    # 1) A abre o caso
    sys_a = _BASE_SYS.format(nome=nome_a, outro=nome_b, postura=postura_a)
    fala_a = None
    for rota in rotas_a:
        try:
            fala_a = _pedir(gw, rota, sys_a,
                            f"CONTEXTO DO MERCADO:\n{ctx}\n\nPERGUNTA: {pergunta}")
            break
        except Exception:
            continue
    blocos.append(f"**{nome_a}:** {fala_a if fala_a else '(indisponível)'}")
    blocos.append("")

    # 2) B rebate (lendo a fala de A)
    sys_b = _BASE_SYS.format(nome=nome_b, outro=nome_a, postura=postura_b)
    msg_b = (
        f"CONTEXTO DO MERCADO:\n{ctx}\n\nPERGUNTA: {pergunta}\n\n"
        f"FALA DO {nome_a}:\n{fala_a or '(ainda veio nada)'}\n\n"
        "Sua vez: rebata com argumento numérico objetivo."
    )
    fala_b = None
    for rota in rotas_b:
        try:
            fala_b = _pedir(gw, rota, sys_b, msg_b)
            break
        except Exception:
            continue
    blocos.append(f"**{nome_b}:** {fala_b if fala_b else '(indisponível)'}")
    blocos.append("")

    # 3) A responde (só se o round 1 rolou inteiro)
    if fala_a and fala_b:
        msg_a2 = (
            f"CONTEXTO DO MERCADO:\n{ctx}\n\nPERGUNTA: {pergunta}\n\n"
            f"SUA FALA ANTERIOR:\n{fala_a}\n\n"
            f"RÉPLICA DO {nome_b}:\n{fala_b}\n\n"
            "Responda em até 3 linhas: onde sua leitura vale, onde não vale, "
            "e qual gatilho objetivo observar."
        )
        try:
            r2 = _pedir(gw, rotas_a[0], sys_a, msg_a2)
            blocos.append(f"**{nome_a} (responde):** {r2}")
        except Exception as e:
            blocos.append(f"**{nome_a} (responde):** (falha: {str(e)[:80]})")
        blocos.append("")

    # 4) Moderador fecha o trato
    infantil = [b for b in blocos if b and not b.startswith("🎯")]
    debate_txt = "\n".join(infantil)[:4000]
    try:
        veredicto = _pedir(
            gw, _MODEL_MOD,
            _SYS_MOD.format(ctx=ctx, debate=debate_txt),
            "Dê o veredicto.",
        )
        blocos.append("---")
        blocos.append(f"⚖️ **MODERADOR**\n\n{veredicto}")
    except Exception as e:
        blocos.append("---")
        blocos.append(f"⚖️ **MODERADOR:** (falha: {str(e)[:80]})")

    return blocos


def contexto_curto() -> str:
    """Snapshot enxuto — reusa o contexto rico do chat."""
    from modules import chat
    return chat.contexto()
