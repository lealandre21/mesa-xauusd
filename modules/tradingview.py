import streamlit as st


def show_tradingview():

    st.iframe(
        "https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD",
        height=700
    )