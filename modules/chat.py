# -*- coding: utf-8 -*-
"""Chat da Mesa: você pergunta, a mesa responde — ao vivo.

Dois motores:
1) LOCAL (regras): CONSULTOR-1 interpreta a pergunta e responde com dados reais.
2) CLAUDE (opcional): com a chave na sidebar, a conversa vai pra API da Anthropic
   com o CONTEXTO DO MERCADO injetado — os analistas "falam" de verdade.
Educacional: nenhum motor recomenda ordem. Sem chave, custo zero.
"""
from modules import dashboard, market, plan, smc, secrets
from modules import calendar
from modules import claude_api, data
from modules.ai import market_analysis

MODOS = {
    "🏛️ CONSELHO — mesa dá parecer": """Você é a MESA XAUUSD: uma equipe de analistas de estudo
(SMC, ICT, Quant, Gestor de Risco, Moderador). Você responde em PT-BR para um
aluno aprendendo Smart Money Concepts para operar OURO (XAUUSD) em conta demo.

Regras:
- Baseie-se SOMENTE no CONTEXTO DO MERCADO; se faltar dado, diga que não tem.
- Resposta curta (máx. ~10 linhas), direta, com números do contexto quando houver.
- Se pedirem decisão de compra/venda, transforme em leitura técnica + gatilho a
  observar + ângulo educacional, e reforce: não é recomendação, conta demo.
- Termine com uma "dica do moderador" de 1 linha.
""",
    "🎓 PROFESSOR — aula passo a passo": """Você é o PROFESSOR-1 da MESA XAUUSD: um professor paciente de SMC/ICT para um
aluno com TDAH (contexto curto, atenção flutuante). PT-BR, acolhedor e sem jargão.

Regras:
- Baseie-se SOMENTE no CONTEXTO DO MERCADO; use o cenário ATUAL como exemplo vivo
  da aula (citar os números reais do contexto deixa a aula concreta).
- ESTRUTURA OBRIGATÓRIA: (1) resposta curta à pergunta em 2-3 linhas;
  (2) "Aula de 1 minuto" com até 4 passos numerados e curtos; (3) uma pergunta
  de verificação de aprendizado ao final.
- Analogias simples (jogos de vida real, filas, leilão). Nada de sobrecarga:
  UM conceito por vez. Repetição é bem-vinda.
- Nunca recomenda ordem; lembra conta demo com gentileza.
""",
    "🥊 DEBATE — analistas discutem entre si": """Você é a MESA XAUUSD em modo DEBATE. Os analistas REAIS discordam entre si:
SMC (estrutura) × ICT (liquidez) × Quant (números) e o Moderador decide PT-BR.

Regras:
- Baseie-se SOMENTE no CONTEXTO DO MERCADO; cite números do contexto.
- Formato: 1a linha "🎯 MESA abre o caso" (a pergunta reformulada); depois
  2-3 falas curtas marcadas como **SMC:**, **ICT:**, **Quant:** divergindo de
  verdade (posturas contrapostas, não eco); fechar com **⚖️ Moderador:** sentando
  o trato em 2 linhas com o plano de observação.
- Máx. 12 linhas no total. Sem recomendação de ordem; conta demo sempre.
""",
}


def prompt_do_modo(modo: str) -> str:
    return MODOS.get(modo, MODOS["🏛️ CONSELHO — mesa dá parecer"])


def contexto():
    """Snapshot completo do painel, em texto, pra alimentar o chat/Claude."""
    p = plan.plano()
    t4, t1, t15 = p["trends"]
    bsl, ssl, eqh, eql = smc.liquidity_map()
    pd_txt, _pos = smc.pd_state()
    aberto_fx, quando_fx = dashboard.mercado_fx()
    preco = data.price()
    evos = calendar.upcoming(True)[:3]
    eventos_txt = "; ".join(
        f"{e['Quando']} {e['Evento']} ({e['Impacto']})" for e in evos
    ) or "nenhum relevante próximo"

    return (
        f"- Agora (Brasília): {dashboard.hora_brt().strftime('%d/%m %H:%M')} · "
        f"sessão: {dashboard.current_session()} · "
        f"XAUUSD real: {'ABERTO' if aberto_fx else 'FECHADO (' + quando_fx + ')'}\n"
        f"- Preço do ouro (proxy PAXG): US$ {data.fmt(preco) if preco else 'sem dado'} · "
        f"spread: {market.spread()}\n"
        f"- Fluxo 4h: {t4} · 1h: {t1} · 15m: {t15}\n"
        f"- BoS (1h): {smc.detect_bos()} · CHoCH: {smc.detect_choch()}\n"
        f"- Faixa 20 candles 1h: {pd_txt}\n"
        f"- FVG 15m: {smc.detect_fvg()} · Order Block: {smc.detect_orderblock()}\n"
        f"- Liquidez 15m: BSL {data.fmt(bsl) if bsl else '-'} · "
        f"SSL {data.fmt(ssl) if ssl else '-'} · "
        f"EQH {'perto' if eqh else '-'} · EQL {'perto' if eql else '-'}\n"
        f"- Plano: {p['headline']} · gatilho: {p['gatilho']}\n"
        f"- Alvo pela estrutura: {data.fmt(p['alvo']) if p['alvo'] else '-'} · "
        f"invalidação: {p['invalidacao']}\n"
        f"- Calendário (USD Alto/Médio): {eventos_txt}"
    )


def interpretar(q: str) -> str:
    """CONSULTOR-1 local: leitura por palavras-chave (PT-BR)."""
    q = (q or "").lower()
    preco = data.price()

    if any(k in q for k in ("preço", "preco", "quanto está", "quanto ta", "cotação")):
        p = plan.plano()
        return (
            f"🥇 Ouro (proxy PAXG): **US$ {data.fmt(preco)}** agora.\n\n"
            f"Fluxo: 4h {p['trends'][0]} · 1h {p['trends'][1]} · 15m {p['trends'][2]}"
        )

    if any(k in q for k in ("o que fazer", "operação", "compra", "venda", "entrada")):
        p = plan.plano()
        checks = "\n".join(
            f"- {('✅' if ok else '⏳')} {texto}" for texto, ok in p["checks"]
        )
        return (
            f"🧭 **{p['headline']}**\n\n{checks}\n\n"
            f"🎯 Gatilho: {p['gatilho']}\n\n"
            f"🏁 Alvo: {data.fmt(p['alvo']) if p['alvo'] else '-'} · "
            f"⛔ Invalida: {p['invalidacao']}\n\n"
            f"📖 Leitura, não recomendação — demo sempre."
        )

    if "fvg" in q or "imbalance" in q or "gap" in q:
        fv = smc.detect_fvg()
        if fv in ("Nenhum ativo", "-"):
            return (
                "🕳️ Nenhum FVG 15m ativo agora. Quando surgir: preço voltar pro gap "
                "e reagir com corpo 15m na direção do fluxo 1h."
            )
        return (
            f"🕳️ FVG ativo: **{fv}**.\n\n"
            f"Esperar: preço retroceder pro gap e REAGIR (corpo fechando na direção). "
            f"Inválido se fechar inteiro do outro lado."
        )

    if "order" in q or "block" in q:
        return (
            f"📦 Order Block: **{smc.detect_orderblock()}**.\n\n"
            f"Esperar mitigação: pavio toca a borda + corpo fecha longe, "
            f"na direção do fluxo 1h."
        )

    if any(k in q for k in ("liquidez", "bsl", "ssl", "varrida", "eqh", "eql")):
        bsl, ssl, eqh, eql = smc.liquidity_map()
        return (
            f"🪤 BSL: {data.fmt(bsl) if bsl else '-'} · SSL: {data.fmt(ssl) if ssl else '-'} · "
            f"EQH {'perto' if eqh else '-'} / EQL {'perto' if eql else '-'}.\n\n"
            f"O importante é a varrida: pavio atravessa, para o stop-hunt, e o corpo volta."
        )

    if any(k in q for k in ("sessão", "horário", "horario", "quando abre", "killzone", "fechado", "aberto")):
        aberto, quando = dashboard.mercado_fx()
        return (
            f"🕐 Sessão: {dashboard.current_session()}.\n\n"
            f"XAUUSD real: {'🟢 ABERTO' if aberto else '🔴 FECHADO — ' + quando}. "
            f"(o proxy PAXG negocia 24/7, mas o ouro 'de verdade' não)"
        )

    if any(k in q for k in ("calendário", "calendario", "evento", "notícia", "noticia", "cpi", "fomc")):
        evos = calendar.upcoming(True)[:3]
        if not evos:
            return "📅 Nenhum evento relevante (USD Alto/Médio) próximo esta semana."
        linhas = "\n".join(
            f"- {e['Impacto']} · {e['Quando']} · {e['Evento']}" for e in evos
        )
        return (
            f"📅 Radar:\n{linhas}\n\n"
            f"Frente de evento 🔴 não é leitura — é aposta."
        )

    if any(k in q for k in ("risco", "lote", "pip", "quanto perder", "quanto ganhar")):
        return (
            "💰 Matemática da mesa:\n\n"
            "- 1 pip (0.10 de preço) = **US$ 10 por lote**\n"
            "- Risco por trade ≤ **1%** da conta\n"
            "- Stop: atrás da estrutura (zona/liquidez), não número mágico\n\n"
            "Digite valores na aba 🎯 Operação → Risco rápido e veja em US$."
        )

    if any(k in q for k in ("viés", "vies", "tendência", "tendencia", "direção", "direcao")):
        p = plan.plano()
        return (
            f"🧲 Viés: 4h **{p['trends'][0]}** · 1h **{p['trends'][1]}** · "
            f"15m **{p['trends'][2]}** · faixa: {smc.pd_state()[0]}\n\n"
            f"Leitura: **{p['headline']}**"
        )

    if any(k in q for k in ("premium", "discount", "caro", "barato")):
        txt, _pos = smc.pd_state()
        return (
            f"⚖️ Faixa 1h: **{txt}**.\n\n"
            f"Premium = metade de cima (caro) · Discount = metade de baixo (barato) · "
            f"50% = equilíbrio."
        )

    # default: resumo geral
    return (
        "📋 **Resumo do momento**\n\n" + market_analysis().strip()
        + "\n\nPergunta específica ajuda: *preço, viés, FVG, liquidez, sessão, "
        "calendário, risco...*"
    )


def render_chat(usar_claude=False, api_key=None, modelo=None, modo=None):
    import streamlit as st

    if "chat_hist" not in st.session_state:
        st.session_state.chat_hist = [
            {"role": "assistant", "texto": (
                "🙋 Mesa disponível! Pergunte: **preço, viés, FVG, liquidez, "
                "sessão, calendário, risco** — respondo com os dados de agora."
            )}
        ]

    for m in st.session_state.chat_hist[-14:]:
        with st.chat_message("user" if m["role"] == "user" else "assistant"):
            st.markdown(m["texto"])

    pergunta = st.chat_input(
        "Pergunte à mesa (ex.: 'tem FVG?', 'o que fazer?', 'quando abre?', 'tem evento?')"
    )

    if pergunta:
        st.session_state.chat_hist.append({"role": "user", "texto": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)

        with st.chat_message("assistant"):
            # Config da IA: hub local detectado no PC (auto) OU chave manual na sidebar.
            gw = secrets.gateway()
            usar_hub = usar_claude and bool(gw)
            usar_nuvem = usar_claude and not gw and bool((api_key or "").strip())

            if usar_hub or usar_nuvem:
                with st.spinner("🤖 A mesa pensa (IA real)..."):
                    hist = [(m["role"], m["texto"]) for m in st.session_state.chat_hist[-8:]]
                    prompt = prompt_do_modo(modo)
                    try:
                        if usar_hub:
                            resposta = claude_api.ask(
                                gw["token"],
                                modelo or gw["model"],
                                prompt + "\n\nCONTEXTO AGORA:\n" + contexto(),
                                hist,
                                base_url=gw["base_url"],
                            )
                        else:
                            resposta = claude_api.ask(
                                api_key.strip(),
                                modelo,
                                prompt + "\n\nCONTEXTO AGORA:\n" + contexto(),
                                hist,
                            )
                    except Exception as e:
                        resposta = (
                            f"⚠️ IA indisponível ({str(e)[:140]}). Respondendo com o motor local:\n\n"
                            + interpretar(pergunta)
                        )
            else:
                resposta = interpretar(pergunta)
            st.markdown(resposta)

        st.session_state.chat_hist.append({"role": "assistant", "texto": resposta})
        st.session_state.chat_hist = st.session_state.chat_hist[-24:]
        st.rerun()
