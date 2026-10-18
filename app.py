import streamlit as st

from datetime import datetime

from modules import data, plan, scan, counselor, chat, diario, dashboard, secrets, voz
from modules.chart import show_chart
from modules.calendar import upcoming
from modules.nota import resumo as nota_resumo
from modules.smc import detect_fvg, detect_orderblock, detect_liquidity, risk_alert, system_logs
from modules.risk import calculate_money
from modules.ai import market_analysis
from modules.market import current_price, spread, market_status
from modules.tradingview import show_tradingview

st.set_page_config(
    page_title="Mesa XAUUSD",
    page_icon="🔥",
    layout="wide"
)

# =====================================
# SIDEBAR
# =====================================

with st.sidebar:
    st.header("⚙️ Config")

    gw = secrets.gateway()
    if gw:
        st.success(f"🤖 Hub de IAs · {secrets.mascarado_cfg(gw)}")
        usar_claude = st.toggle("🧠 Ligar IA real", value=False)
        rotas = ["auto/claude-haiku", "auto/claude-sonnet", "auto/best-free",
                 "auto/best-chat", "auto/fast", "auto/thrifty"]
        modelo = st.selectbox("Modelo", rotas, index=0)
        if usar_claude:
            st.caption("A conversa passa pelo SEU hub local (798 modelos).")
        else:
            st.caption("Motor local grátis ativo. Ligue pra IA conversar de verdade.")
    else:
        usar_claude = st.toggle("🤖 Ligar Claude (chave nuvem)", value=False)
        api_key = ""
        modelo = "claude-sonnet-4-5"
        if usar_claude:
            api_key = st.text_input("ANTHROPIC_API_KEY", type="password")
            modelo = st.text_input("Modelo", value=modelo)
        else:
            api_key = ""
        api_key = api_key

    st.divider()

    aberto_fx, quando_fx = dashboard.mercado_fx()
    st.write("🟢 **XAUUSD aberto**" if aberto_fx
             else f"🔴 **XAUUSD fechado** · {quando_fx}")
    st.write(f"🕐 {dashboard.current_session()}")
    st.write(f"🧭 {plan.plano()['headline'].split(' —')[0]}")

    st.divider()
    st.caption("📚 Educacional · conta demo SEMPRE · nada é recomendação.")

# =====================================
# TOPO
# =====================================

st.title("🔥 Mesa XAUUSD")
counselor.render()


@st.fragment(run_every="60s")
def painel_vivo():
    diario.log()

    cand = data.candles("1h", 3)
    delta_txt = (
        f"{cand[-1]['c'] - cand[0]['c']:+.2f} (1h)"
        if len(cand) >= 2 else None
    )

    a1, a2, a3, a4 = st.columns([1.35, 1.2, 0.7, 1.15])
    a1.metric("🥇 Preço", current_price(), delta=delta_txt)
    a2.metric("🕐 Sessão", dashboard.current_session())
    a3.metric("🧠 Confiança", dashboard.confidence())
    a4.metric("📊 Clima", market_status())

    st.caption(
        f"{datetime.now().strftime('%d/%m · %H:%M')} (Brasília) · Spread {spread()} · "
        f"{'🟢 aberto' if aberto_fx else '🔴 fechado (' + quando_fx + ')'} · 🫀 60s"
    )

    tipo_alerta, msg = risk_alert()
    if "prev_alert" in st.session_state and st.session_state.prev_alert != tipo_alerta:
        st.toast(msg, icon="⚠️" if tipo_alerta == "warn" else "🤖")
    st.session_state.prev_alert = tipo_alerta

    # 🪤 alerta de varrida de liquidez (BSL/SSL): pavio atravessa e corpo volta
    from modules import alerts
    v = alerts.varredura()
    if v and st.session_state.get("prev_sweep") != v[0]:
        st.toast(f"🪤 {v[1]} — {v[2]}", icon="🪤")
        st.session_state["sweep_recente"] = (v[1], v[2])
    if v:
        st.session_state.prev_sweep = v[0]
        st.warning(f"🪤 **{v[1]}** · {v[2]}\n\n*É leitura, não ordem — confirme com corpo no TF maior.*")
    elif st.session_state.get("prev_sweep"):
        st.session_state.prev_sweep = None
        st.session_state.pop("sweep_recente", None)


painel_vivo()
st.divider()

# =====================================
# GRÁFICO + PLANO (o coração)
# =====================================

g1, g2 = st.columns([7, 5])

with g1:
    tf = st.radio("TF", ["15m", "1h", "4h"], horizontal=True, label_visibility="collapsed")
    show_tradingview(tf, height=520)
    with st.expander("📐 Leitura SMC anotada (zonas/BoS/FVG desenhadas)"):
        show_chart(tf, height=430)

with g2:
    p = plan.plano()
    st.markdown(f"### 🧭 {p['headline']}")
    for texto, ok in p["checks"]:
        st.write(("✅" if ok else "⏳") + " " + texto)
    st.write(f"**🎯 Gatilho:** {p['gatilho']}")
    st.write(f"**🏁 Alvo:** {data.fmt(p['alvo']) if p['alvo'] else '-'} · "
             f"**⛔ Invalida:** {p['invalidacao']}")
    st.caption("💡 Gatilho é SEMPRE corpo fechando — pavio não conta.")

    if st.button("🔊 Ouvir o plano (voz)"):
        with st.spinner("🎙️ Narrando o plano..."):
            texto_voz = voz.src()
            mp3 = voz.gerar(texto_voz)
        if mp3:
            st.audio(mp3, format="audio/mp3", autoplay=True)
            st.caption(f"🎙️ Voz id: {voz.chave(texto_voz)} · edge-tts Antônio")
        else:
            st.warning("Voz indisponível agora (rede?) — o plano tá escrito acima. 👆")

st.divider()

# =====================================
# CHAT + ARENA
# =====================================

st.subheader("💬 Chat com a Mesa (ao vivo)")

modo_ia = st.selectbox(
    "🎭 Modo da conversa",
    list(chat.MODOS.keys()),
    index=0,
    horizontal=False,
)

chat.render_chat(usar_claude=usar_claude, api_key=api_key, modelo=modelo, modo=modo_ia)

with st.expander("🥊 Arena multi-IA (2 IAs de verdade discutindo)"):
    st.caption("🤖 CLAUDE-Estrutura vs 🧪 QUANT-Fluxo (free) · moderador fecha · 4 chamadas por rodada.")

    perg_debate = st.text_input(
        "Pergunta pro debate",
        value="Tem setup na mesa agora ou é dia de ficar de fora?",
        key="debate_perg",
    )
    if st.button("🥊 Rodar o debate", type="primary"):
        from modules import debate
        with st.spinner("A arena esquenta... (30-90s)"):
            try:
                nova = debate.rodar(perg_debate)
            except Exception as e:
                nova = [f"⚠️ Falha na arena: {str(e)[:140]}"]
        st.session_state["debate_blocos"] = (
            st.session_state.get("debate_blocos", []) + nova
        )[-20:]

    for f_ in st.session_state.get("debate_blocos", []):
        st.markdown(f_)

    if st.session_state.get("debate_blocos") and st.button("🧹 Limpar arena"):
        st.session_state["debate_blocos"] = []
        st.rerun()

# =====================================
# GAVETAS (tudo que Não é urgência)
# =====================================

with st.expander("🧯 Risco rápido + 📅 Agenda (real)"):
    ri1, ri2, ri3, ri4 = st.columns(4)
    with ri1:
        entrada = st.number_input("Entrada", value=None, key="ent", format="%.2f")
    with ri2:
        stop = st.number_input("Stop", value=None, key="stp", format="%.2f")
    with ri3:
        take = st.number_input("Alvo", value=None, key="tk", format="%.2f")
    with ri4:
        lotes = st.number_input("Lotes", value=0.10, min_value=0.01, step=0.01)

    m = calculate_money(entrada, stop, take, lotes)
    rm1, rm2, rm3, rm4 = st.columns(4)
    rm1.metric("R:R", m.get("rr", m.get("erro", "—")))
    rm2.metric("Pips risco", m.get("pips_risco", "—"))
    rm3.metric("Risco US$", m.get("dol_risco", "—"))
    rm4.metric("Ganho US$", m.get("dol_premio", "—"))
    st.caption("💡 1 pip = US$ 10/lote · risco ≤ 1% da conta · demo.")

    st.subheader("📅 Radar de eventos")
    evos = upcoming(True)[:5]
    if evos:
        for ev in evos:
            icone = "🔴" if "Alto" in ev["Impacto"] else "🟡"
            st.write(f"{icone} **{ev['Quando']}** · {ev['Evento']}")
        st.caption("A frente de evento 🔴 não é leitura — é aposta.")
    else:
        st.info("Nada relevante nas próximas horas. 🍃")

with st.expander("🗺️ Zonas + censo (estudo profundo)"):
    st.markdown(plan.bar_faixa(), unsafe_allow_html=True)
    zv1, zv2 = st.columns(2)
    cartoes = plan.zonas_explicadas()
    for coluna, grupo in ((zv1, cartoes[:2]), (zv2, cartoes[2:])):
        with coluna:
            for card in grupo:
                st.container(border=True).write(
                    f"**{card['nome']}** — {card['status']}\n\n"
                    f"*O que esperar:* {card['esperar']}\n\n"
                    f"*🎯 Gatilho:* {card['gatilho']} · *⛔ Invalida:* {card['invalida']}"
                )
    st.subheader("🌐 Censo multimercado")
    st.table(scan.scan())
    alt = scan.foco_alternativo()
    if alt:
        st.info(f"🛰️ Ouro sem setup? Olho no **{alt[0]}** — {alt[1]} · **{alt[2]}**.")
    else:
        st.caption("🛰️ Nenhum par alternativo alinhado — paciência também é posição.")

with st.expander("📊 NOTA DA MESA (backtest honesto da leitura)"):
    texto_nota, exemplos = nota_resumo()
    st.markdown(texto_nota)
    if exemplos:
        for quando, direcao, delta, marca in exemplos:
            st.write(f"{marca} `{quando}` · chamou **{direcao}** · mercado andou {delta:+.2f}")
        st.caption("💬 A nota cresce com os dias de diário. Leitura sem cobrança é opinião; com cobrança é método.")

with st.expander("🩺 Sistema"):
    st.info(market_analysis())

    tipo_alerta, msg_alerta = risk_alert()
    (st.warning if tipo_alerta == "warn" else st.info)(msg_alerta)

    gw_ui = secrets.gateway()
    if gw_ui:
        st.write(f"Hub: `{gw_ui['base_url']}` · `{secrets.mascarado_cfg(gw_ui)}` · "
                 "catálogo em `hub-modelos.md`")

    st.subheader("📜 Logs")
    for icone, msg_log in system_logs():
        st.write(icone, msg_log)

    st.success("🫀 Online · dados reais (gold-api + Binance PAXG) · demo sempre")
