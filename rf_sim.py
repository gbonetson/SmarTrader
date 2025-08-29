import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- Cashflows hardcodeados ---
AL41_CASHFLOWS = [
    {"fecha": "2027-12-09", "cupon": 9.75, "amortizacion": 4.0},
    {"fecha": "2028-12-09", "cupon": 9.75, "amortizacion": 4.0},
    {"fecha": "2029-12-09", "cupon": 9.75, "amortizacion": 4.0},
    {"fecha": "2030-12-09", "cupon": 9.75, "amortizacion": 4.0},
    {"fecha": "2031-12-09", "cupon": 9.75, "amortizacion": 4.0},
    {"fecha": "2032-12-09", "cupon": 9.75, "amortizacion": 4.0},
    {"fecha": "2033-12-09", "cupon": 9.75, "amortizacion": 4.0},
    {"fecha": "2034-12-09", "cupon": 9.75, "amortizacion": 4.0},
    {"fecha": "2035-12-09", "cupon": 9.75, "amortizacion": 4.0},
    {"fecha": "2036-12-09", "cupon": 9.75, "amortizacion": 4.0},
    {"fecha": "2037-12-09", "cupon": 9.75, "amortizacion": 4.0},
    {"fecha": "2038-12-09", "cupon": 9.75, "amortizacion": 4.0},
    {"fecha": "2039-12-09", "cupon": 9.75, "amortizacion": 4.0},
    {"fecha": "2040-12-09", "cupon": 9.75, "amortizacion": 4.0},
    {"fecha": "2041-12-09", "cupon": 9.75, "amortizacion": 36.0},
]

AE38_CASHFLOWS = [
    {"fecha": "2032-12-15", "cupon": 8.5, "amortizacion": 14.3},
    {"fecha": "2033-12-15", "cupon": 8.5, "amortizacion": 14.3},
    {"fecha": "2034-12-15", "cupon": 8.5, "amortizacion": 14.3},
    {"fecha": "2035-12-15", "cupon": 8.5, "amortizacion": 14.3},
    {"fecha": "2036-12-15", "cupon": 8.5, "amortizacion": 14.3},
    {"fecha": "2037-12-15", "cupon": 8.5, "amortizacion": 14.3},
    {"fecha": "2038-12-15", "cupon": 8.5, "amortizacion": 14.4},
]

# Otros bonos simplificados y Lecaps
BONOS = {
    "AL30": {"par": 100, "coupon": 0.05, "freq": 2, "maturity": "2030-12-31"},
    "GD30": {"par": 100, "coupon": 0.045, "freq": 2, "maturity": "2030-07-09"},
    "US10Y": {"par": 100, "coupon": 0.035, "freq": 2, "maturity": "2034-08-15"},
    "LECAP 6m": {"par": 100, "coupon": 0.0, "freq": 1, "maturity": (datetime.today() + timedelta(days=180)).strftime("%Y-%m-%d")},
    "LECAP 1y": {"par": 100, "coupon": 0.0, "freq": 1, "maturity": (datetime.today() + timedelta(days=365)).strftime("%Y-%m-%d")},
}

def generar_flujos(bono_sel, precio, cantidad, años=10):
    """Genera fechas, flujos, P&L vs paridad y aplica cantidad"""
    hoy = datetime.today()
    flujos_list = []

    # Elegimos cashflows reales o simplificados
    if bono_sel == "AL41":
        cashflows = AL41_CASHFLOWS
    elif bono_sel == "AE38":
        cashflows = AE38_CASHFLOWS
    else:
        bono = BONOS[bono_sel]
        maturity = datetime.strptime(bono["maturity"], "%Y-%m-%d")
        freq = bono["freq"]
        n_pagos = int(((maturity - hoy).days / 365) * freq)
        fechas = [hoy + timedelta(days=int(365/freq)*i) for i in range(1, n_pagos+1)]
        flujos = np.full(n_pagos, bono["par"]*bono["coupon"]/freq)
        if len(flujos) > 0:
            flujos[-1] += bono["par"]  # último flujo incluye el principal
        else:
            # si no hay flujos proyectados, agregamos el principal al final del período proyectado
            fechas.append(hoy + timedelta(days=365*años))
            flujos = np.array([bono["par"]])
        cashflows = [{"fecha": f.strftime("%Y-%m-%d"), "cupon": flujos[i], "amortizacion": 0} for i,f in enumerate(fechas)]
    
    # Filtramos según cantidad de años
    fin = hoy + timedelta(days=365*años)
    for cf in cashflows:
        fecha = datetime.strptime(cf["fecha"], "%Y-%m-%d")
        if fecha <= fin:
            # flujo total = cupon + amortización sobre cantidad de bonos
            saldo_vivo = 100  # aproximación, para simplificación
            flujo_total = (cf["cupon"]/100 * saldo_vivo + cf["amortizacion"]) * cantidad
            flujos_list.append({"fecha": cf["fecha"], "flujo": flujo_total})

    # Crear DataFrame
# Crear DataFrame y calcular acumulado
    df = pd.DataFrame(flujos_list)
    df["Acumulado"] = df["flujo"].cumsum()

    # P&L vs paridad: asumimos que paridad = precio / par
    paridad = np.linspace(80, 120, 100)
    pnl = (paridad - precio) * cantidad

    return df, paridad, pnl

def RentaFija():
    st.title("💵 TradeSimulator - Renta Fija")

    # --- Inputs ---
    col1, col2, col3, col4 = st.columns([2,2,2,2])

    with col1:
        bono_sel = st.selectbox("Seleccioná bono/lecap", ["AL41", "AE38", "AL30", "GD30", "US10Y", "LECAP 6m", "LECAP 1y"])
    
    with col2:
        precio = st.number_input("Precio de mercado actual", min_value=0.0, value=80.0, step=0.5)
    
    with col3:
        cantidad = st.number_input("Cantidad de bonos", min_value=1, value=10, step=1)
    
    with col4:
        años = st.number_input("Cantidad de años a proyectar flujos", min_value=1, value=10, step=1)

    df, paridad, pnl = generar_flujos(bono_sel, precio, cantidad, años)

    st.subheader("📊 Flujos de caja proyectados")
    st.dataframe(df)

    st.subheader("📊 P&L vs Paridad")
    fig = go.Figure()
    # Línea P&L en rojo si debajo de precio de compra, verde si arriba
    mask_left = paridad <= precio
    mask_right = paridad >= precio
    fig.add_trace(go.Scatter(x=paridad[mask_left], y=pnl[mask_left], mode='lines', line=dict(color="red"), name="Pérdida"))
    fig.add_trace(go.Scatter(x=paridad[mask_right], y=pnl[mask_right], mode='lines', line=dict(color="green"), name="Ganancia"))
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    fig.add_vline(x=precio, line_dash="dash", line_color="blue", annotation_text="Precio de compra", annotation_position="top")
    fig.update_layout(title=f"P&L de {bono_sel}", xaxis_title="Paridad del bono", yaxis_title="Ganancia/Pérdida", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
