import streamlit as st

from datetime import datetime

from modules import data, plan, scan, counselor, chat, diario, dashboard, secrets, voz, indicadores, news, mt5_data
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
        api_key = ""  # hub cuida do token por dentro (chat usa gw["token"])
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

# =====================================
# NOTÍCIAS (faixa rolando + manchetes) — só informação, não é leitura
# =====================================

try:
    news_itens = news.manchetes()
except Exception:
    news_itens = []

if news_itens:
    news.banda(news_itens)
    with st.expander("📰 Manchetes do forex (RSS grátis · 5 min de cache)"):
        news.lista(news_itens)

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

# =====================================
# TERMÔMETROS (RSI · ATR · pressão) — confirmação, nunca sinal
# =====================================

try:
    ind = indicadores.leitura(tf)
except Exception:
    ind = None

if ind and ind.get("rsi") is not None:
    t1, t2, t3 = st.columns(3)
    with t1:
        st.metric("🌡️ RSI", f"{ind['rsi']:.1f}")
        st.caption(ind["rsi_txt"])
    with t2:
        st.metric("📏 Volatil (ATR)", data.fmt(ind["atr"]))
        st.caption(ind["atr_txt"])
    with t3:
        pc, pv = ind["press"] or (None, None)
        st.metric("⚖️ Pressão", f"{pc:.0f}%⬆ / {pv:.0f}%⬇" if pc is not None else "-")
        st.caption(ind["press_txt"])

# =====================================
# MODO CONTA DEMO (execução assistida) — só demo, 2-passos, stop obrigatório
# =====================================

from modules import trades as tr_m  # noqa: E402

st.subheader("🧪 Modo Conta Demo (entrada assistida pelo plano)")

demo_acct = mt5_data.acct()
if not demo_acct:
    st.info("🔌 Ponte MT5 desligada — liga o terminal pra usar entradas. "
            "A Mesa continua lendo normal (proxy Binance).")
elif not demo_acct.get("demo"):
    st.error("⛔ CONTA NÃO-DEMO detectada — botões bloqueados por segurança.")
else:
    st.caption(f"Conta `{demo_acct['login']}` @ {demo_acct['servidor']} · "
               f"saldo {demo_acct['saldo']:.2f} {demo_acct['moeda']} · DEMO confirmada")

    card = tr_m.cartao()
    if card.get("sem_setup"):
        st.info(f"🧭 {card['headline']} — sem gatilho de entrada agora. "
                "Esperar é executar também.")
    else:
        c1, c2, c3, c4 = st.columns([1.1, 1.1, 1.1, 1.3])
        c1.metric("🎯 Entrada (mercado)", data.fmt(card["preco"]))
        c2.metric("⛔ Stop", data.fmt(card["stop"]))
        c3.metric("🏁 Alvo", data.fmt(card["alvo"]))
        c4.metric("⚖️ R:R", f"{card['rr']:.2f}" if card.get("rr") else "auto")
        st.caption(f"📋 Plano: **{card['headline']}** · risco estimado "
                   f"US$ {tr_m.risco_dinheiro(card['preco'], card['stop'], *mt5_data.risco() or (None, None)):.2f} (lote 0.01) · "
                   f"invalidação: {card['invalida_txt'] if not card.get('rr_baixo') else 'R:R insuficiente — plano recusado'}")
        if card.get("rr_baixo"):
            st.warning(f"⚠️ R:R {card['rr_baixo']:.2f} < 1.0 — execução travada. "
                       "Esperar setup melhor é trade bom.")
        else:
            st.markdown(f"✅ **R:R {card['rr']:.2f}** · gatilho: *{card['gatilho']}*")

            lado = card["direcao"]
            if st.checkbox("⚡ Confirmo: conta DEMO, li o plano inteiro",
                           value=st.session_state.get("demo_ok", False)):
                st.session_state["demo_ok"] = True
                boa = lado == "compra"
                n1 = "🟢 ARMAR COMPRA" if boa else "🔴 ARMAR VENDA"
                if st.button(n1, type="secondary"):
                    st.session_state["armado"] = (lado, datetime.now().timestamp())
                armado = st.session_state.get("armado")
                if armado and armado[0] == lado and (datetime.now().timestamp() - armado[1]) < 240:
                    st.write(f"🔒 **Arma armada** — {lado.upper()} @ {data.fmt(card['preco'])} · "
                             f"SL {data.fmt(card['stop'])} · TP {data.fmt(card['alvo'])} · lote 0.01")
                    st.write(f"*Confirma em {(240 - int(datetime.now().timestamp() - armado[1]))}s*")
                    if st.button(f"🔥 **CONFIRMAR {lado.upper()}** — enviar ordem (lote 0.01)",
                                 type="primary" if boa else "primary"):
                        st.session_state["armado"] = None
                        with st.spinner("Enviando pra bridge..."):
                            resp = mt5_data.enviar(lado, 0.01, card["stop"], card["alvo"])
                        if resp and resp.get("ok"):
                            tr_m.registra({
                                "quando": tr_m.agora(), "tipo": "demo",
                                "symbol": resp["symbol"], "direcao": lado,
                                "lote": resp["lote"], "entrada": resp["preco"],
                                "stop": resp["sl"], "alvo": resp["tp"],
                                "plano": card["headline"], "ticket": resp["ticket"],
                            })
                            st.toast(f"Ordem no ar! ticket {resp['ticket']}", icon="✅")
                            st.success(f"💰 **{lado.upper()} no ar** — ticket `{resp['ticket']}` · "
                                       f"entrada {data.fmt(resp['preco'])} · SL {data.fmt(resp['sl'])} · "
                                       f"TP {data.fmt(resp['tp'])}")
                        else:
                            st.error(f"Corretor recusou: {((resp or {}).get('erro', 'sem resposta'))}")
                elif armado and armado[0] != lado:
                    st.session_state["armado"] = None

# ---- posições abertas ----
pos_ = mt5_data.positions()
if pos_:
    st.markdown("##### 📈 Posições abertas")
    for p in pos_:
        cor_sinal = "🟢" if p["direcao"] == "compra" else "🔴"
        lc1, lc2, lc3, lc4 = st.columns([1.5, 1.2, 1.8, 0.9])
        lc1.write(f"{cor_sinal} **{p['direcao']}** `{p['ticket']}` · lote {p['lote']}")
        lc2.write(f"entrou **{data.fmt(p['entrada'])}**")
        lc3.write(f"SL {data.fmt(p['sl'])} · TP {data.fmt(p['tp'])}")
        lc4.write(f"{'🟢' if p['lucro'] >= 0 else '🔴'} **${p['lucro']:+.2f}**")
        if st.button(f"✖ Fechar {p['ticket']}", key=f"f{p['ticket']}"):
            r = mt5_data.fechar(p["ticket"])
            if r and r.get("ok"):
                st.toast(f"Posição {p['ticket']} fechada (lucro {p['lucro']:+.2f})", icon="✅")
                st.rerun()
            else:
                st.error(f"Fecho recusado: {(r or {}).get('erro', 'sem resposta')}")
elif mt5_data.alive():
    st.caption("📈 Nenhuma posição aberta agora.")

st.divider()

# =====================================
# CHAT + ARENA
# =====================================

st.subheader("💬 Chat com a Mesa (ao vivo)")

modo_ia = st.selectbox(
    "🎭 Modo da conversa",
    list(chat.MODOS.keys()),
    index=0,
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

    # status da ponte MT5 (broker real)
    from modules import mt5_data
    v_tick = mt5_data.tick()
    if v_tick:
        st.success(f"📊 Broker real: **{v_tick['symbol']}** · spread US$ {v_tick['spread']} "
                   f"· conta `{(mt5_data.acct() or {}).get('login', '—')}`")
        st.caption("Candles vêm do terminal MT5 (Python 3.12 + mt5_server). "
                   "Pressão de volume segue lendo a Binance (proxy).")
    else:
        st.caption("📊 Broker real (MT5) offline — usando gold-api + Binance PAXG (proxy). "
                   "Liga o terminal pra dados de broker.")

    st.success("🫀 Online · dados reais (MT5 broker + gold-api + Binance PAXG) · demo sempre")
