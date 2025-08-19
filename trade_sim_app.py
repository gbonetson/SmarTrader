import streamlit as st
from rv_sim import RentaVariable
from rf_sim import RentaFija
from opt_sim import Opt_SIM

def TradeSIMS():
    st.subheader("📊 TradeSimulator")

    modo = st.radio("Seleccioná instrumento", ["Renta Variable", "Renta Fija", "Opciones"])
    
    if modo == "Renta Variable":
        render_RV()
    elif modo == "Renta Fija":
        render_RF()
    elif modo == "Opciones":
        render_opt_sim()

def render_RV():
    RentaVariable()

def render_RF():
    RentaFija()

def render_opt_sim():
    Opt_SIM()