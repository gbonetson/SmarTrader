import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from data_fetch import fetch_ticker_info
from dcf import dcf_fmp

def RentaVariable():
    st.title("📈 TradeSimulator - Renta Variable")

    # --- Inputs básicos ---
    st.subheader("Parámetros de la operación")
    ticker = st.text_input("Ticker", value="AAPL").upper()
    spot = float(fetch_ticker_info(ticker)['price'])

    precio_actual = st.number_input("Precio", min_value=0.0, value=spot, step=0.5)
    usar_precio_actual = st.checkbox("Usar precio actual como precio de entrada", value=True)

    if usar_precio_actual:
        precio_entrada = precio_actual
    else:
        precio_entrada = st.number_input("Precio de entrada", min_value=0.0, value=precio_actual, step=0.5)

    cantidad = st.number_input("Cantidad de acciones", min_value=1, value=100, step=1)

    # --- Inputs para DCF ---
    st.subheader("Parámetros de Valuación (DCF)")

    col1, col2, col3 = st.columns([2,2,2])
    with col1:
        wacc = st.number_input(
            "WACC",
            min_value=0.01, max_value=0.3, value=0.08, step=0.005,
            help="Costo promedio ponderado de capital.\n\n"
                "- Empresas grandes/tecnológicas: 6–9%\n"
                "- Empresas medianas/cíclicas: 9–11%\n"
                "- Empresas emergentes/pequeñas: 12–15%+"
        )
    with col2:
        g = st.number_input(
            "Crecimiento perpetuo (g)",
            min_value=-0.05, max_value=0.1, value=0.02, step=0.005,
            help="Tasa de crecimiento a perpetuidad.\n\n"
                "- Conservador: 1–2%\n"
                "- Moderado: 2–3%\n"
                "- Arriesgado: 4–5%+"
        )
    with col3:
        years_projection = st.number_input(
            "Años de proyección",
            min_value=3, max_value=15, value=5, step=1,
            help="Horizonte de proyección de flujos.\n\n"
                "- Común en análisis: 5 años\n"
                "- Más detallado: 7–10 años\n"
                "- Startups/alta incertidumbre: 3 años"
        )

    # --- Cálculo DCF ---
    dcf_per_share = None
    try:
        dcf_result = dcf_fmp(ticker,
                            years_projection=years_projection,
                            wacc=wacc,
                            g=g)
        dcf_per_share = dcf_result["intrinsic_value_per_share"]
        diff_pct = (dcf_per_share - spot) / spot * 100
        pnl_theoretical = (dcf_per_share - precio_entrada) * cantidad

        df = pd.DataFrame([{
            "DCF / Acción (USD)": round(dcf_per_share, 2),
            "Precio Spot (USD)": round(spot, 2),
            "Diferencia %": round(diff_pct, 2),
            "P&L Teórico (USD)": round(pnl_theoretical, 2)
        }])

        st.subheader("📊 Resultado DCF")
        st.table(df)

    except Exception as e:
        st.error(f"Error en el cálculo del DCF: {e}")

    # --- Simulación de precios ---
# --- Simulación de precios ---
    if dcf_per_share is not None:
        min_price = min(precio_actual * 0.7, dcf_per_share * 0.9)
        max_price = max(precio_actual * 1.3, dcf_per_share * 1.1)
    else:
        min_price = precio_actual * 0.7
        max_price = precio_actual * 1.3

    precios = np.linspace(min_price, max_price, 200)
    pnl = (precios - precio_entrada) * cantidad




    break_even = precio_entrada

    fig = go.Figure()
    mask_left = precios <= break_even
    fig.add_trace(go.Scatter(x=precios[mask_left], y=pnl[mask_left],
                             mode='lines', line=dict(color="red"), name="P&L (Pérdida)"))

    mask_right = precios >= break_even
    fig.add_trace(go.Scatter(x=precios[mask_right], y=pnl[mask_right],
                             mode='lines', line=dict(color="green"), name="P&L (Ganancia)"))

    # Línea horizontal en 0
    fig.add_hline(y=0, line_dash="dash", line_color="black")

    # Línea vertical en break-even
    fig.add_vline(x=break_even, line_dash="dash", line_color="blue",
                  annotation_text="Break-even", annotation_position="top")

    # --- Punto de valor intrínseco ---
    if dcf_per_share is not None:
        if dcf_per_share > break_even:
            color = "green"
        elif dcf_per_share < break_even:
            color = "red"
        else:
            color = "gray"

        pnl_intrinsic = (dcf_per_share - precio_entrada) * cantidad
        fig.add_trace(go.Scatter(
            x=[dcf_per_share],
            y=[pnl_intrinsic],
            mode="markers+text",
            marker=dict(size=12, color=color, symbol="circle"),
            name="Valor Intrínseco",
            text=["Valor Intrínseco"],
            textposition="top center"
        ))

    fig.update_layout(
        title=f"Simulación P&L - {ticker}",
        xaxis_title="Precio del activo",
        yaxis_title="Ganancia/Pérdida",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)
