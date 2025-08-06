# options_app.py
import streamlit as st
from datetime import datetime
import plotly.graph_objects as go
from data_fetch import fetch_option_exp, fetch_option_chain, fetch_ticker_info
from analytics import black_scholes

def render_options_workstation():
    st.subheader("🧮 Options Workstation")

    ticker = st.text_input("Ticker", value="AAPL").upper()

    expirations = fetch_option_exp(ticker)
    opt_type = st.radio("Tipo de contrato", ["Calls", "Puts"])
    exp_date = st.selectbox("Vencimiento", sorted(expirations))
    chain = fetch_option_chain(ticker, exp_date)
    if opt_type == "Calls":
        df = chain.calls
    if opt_type == "Puts":
        df = chain.puts

    strikes = df['strike'].tolist()
    last_price = df['lastPrice'].tolist()
    volume = df['volume'].tolist()
    implied_vol = df['impliedVolatility'].tolist()
    spot = fetch_ticker_info(ticker)['price']
    exp_date_dt = datetime.strptime(exp_date, '%Y-%m-%d')
    current_date = datetime.today()
    T = ((exp_date_dt - current_date).days) / 365

    col1, col2 = st.columns([2, 2])
    with col1:
        min_strike = st.selectbox("Rango de bases", sorted(strikes))
    with col2:
        max_strike = st.selectbox(" ", sorted(strikes))

    # Checkbox para mostrar precios teóricos Black-Scholes
    show_bs = st.checkbox("Mostrar precios Black-Scholes", value=False)

    if min_strike > max_strike:
        st.write("no seas down")
    else:
        mult = strikes[1] - strikes[0]
        sub_strikes = []
        sub_volume = []
        sub_last_prices = []
        black_scholes_prices = []

        sub_strikes.append(min_strike)
        a = (max_strike - min_strike) / mult
        for i in range(int(a)):
            sub_strikes.append(min_strike + ((i + 1) * mult))

        for i in range(len(strikes)):
            if strikes[i] == min_strike:
                n1 = i
            if strikes[i] == max_strike:
                n2 = i
        for i in range(n2 - n1 + 1):
            sub_volume.append(volume[n1 + i])
            sub_last_prices.append(last_price[n1 + i])
            black_scholes_prices.append(black_scholes(spot, strikes[n1 + i], T, implied_vol[n1 + i], opt_type))

        # Gráfico volumen
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=sub_strikes,
            y=sub_volume,
            name="Volumen",
            yaxis="y",
            marker=dict(color="deepskyblue", opacity=0.75)
        ))
        fig.update_layout(
            template="plotly_dark",
            xaxis_title="Strikes",
            yaxis_title="Volumen",
            margin=dict(t=20, l=60, r=20, b=20),
            xaxis_rangeslider_visible=False,
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        # Gráfico precio (y eventualmente BS)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=sub_strikes,
            y=sub_last_prices,
            name="Precio de mercado",
            yaxis="y",
            marker=dict(color="gray", opacity=0.3)
        ))

        if show_bs:
            fig2.add_trace(go.Bar(
                x=sub_strikes,
                y=black_scholes_prices,
                name="Precio Black-Scholes",
                yaxis="y",
                marker=dict(color="orange", opacity=0.6)
            ))

        fig2.update_layout(
            template="plotly_dark",
            xaxis_title="Strikes",
            yaxis_title="Precio",
            margin=dict(t=20, l=60, r=20, b=20),
            xaxis_rangeslider_visible=False,
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.subheader("Volumen de opciones")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Precio de opciones")
        st.plotly_chart(fig2, use_container_width=True)
