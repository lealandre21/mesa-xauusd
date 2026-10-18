import streamlit as st

# TF da Mesa → intervalo do widget TradingView
TV_TF = {"15m": "15", "1h": "60", "4h": "240"}


def show_tradingview(tf: str = "15m", height: int = 520, rsi: bool = True):
    """Gráfico TradingView embutido (tema dark, fuso de Brasília).

    - tf: timeframe ("15m", "1h", "4h") — vira o intervalo do widget.
    - rsi: anexa o estudo de RSI padrão do TradingView (conferência visual).
    """
    interval = TV_TF.get(tf, "15")
    url = (
        "https://s.tradingview.com/widgetembed/?symbol=OANDA%3AXAUUSD"
        f"&interval={interval}"
        "&theme=dark&style=1&locale=br"
        "&timezone=Etc%2FGMT%2B3"              # BRT (UTC-3) com nome "GMT+3" no padrão do TradingView
        "&withdateranges=1&hide_side_toolbar=0"
        "&allow_symbol_change=1&save_image=0"
    )
    if rsi:
        url += "&studies=RSI%40tv-basicstudies"
    st.iframe(url, height=height)
