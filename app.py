import streamlit as st
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd
import os
import time
from balance_sheet import extract_filings
from options_app import render_options_workstation

# ---------- RENDER ----------
st.set_page_config(layout="wide", page_title="SmarTrader")

st.markdown("<h1 style='text-align: center; padding-top: 0;'>The SmarTrader terminal</h1>", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
st.sidebar.title("SmarTrader")
tab = st.sidebar.radio("Navegación", ["Terminal", "Options Workstation"])
def render_equity_terminal():
    with st.sidebar:
        ticker = st.text_input("Ticker", value="AAPL").upper()
        st.write("Período del gráfico")
        period = st.selectbox("Periodo", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=2)
        st.write("Intervalo")
        interval = st.selectbox("Intervalo", ["1d", "1wk", "1mo"], index=0)
        show_ema = st.checkbox("EMA", value=True)
        show_rsi = st.checkbox("RSI", value=True)
        show_volume = st.checkbox("Volumen", value=True)

    # ---------------- DESCARGA DE DATOS ----------------

    @st.cache_data
    def fetch_ticker_info(ticker):
        try:
            yf_ticker = yf.Ticker(ticker)
            info = yf_ticker.info
            return {
                "name": info.get("longName", ticker),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "country": info.get("country", "N/A"),
                "website": info.get("website", ""),
                "description": info.get("longBusinessSummary", ""),
                "market_cap": info.get("marketCap", None),
                "price": info.get("currentPrice", None),
                "pe_ratio": info.get("trailingPE", None),
                "pb_ratio": info.get("priceToBook", None),
                "dividend_yield": info.get("dividendYield", None),
                "currency": info.get("currency", "USD"),
            }
        except Exception as e:
            return {"error": str(e)}

    @st.cache_data
    def fetch_price_history(ticker, period, interval):
        df = yf.download(ticker, period=period, interval=interval)
        if df.empty:
            raise ValueError("DataFrame vacío. Verificá el ticker.")

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Forzar columnas a tipo numérico
        for col in ["Open", "High", "Low", "Close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)
        df.index = pd.to_datetime(df.index)
        return df

    def fetch_balance_path(ticker, timeout=10):
        base_path = f"./sheets/{ticker}_bs.html"
        if os.path.exists(base_path):
            return base_path 
        else:
            extract_filings(ticker, save_as= base_path)
            start_time = time.time()
            while not os.path.exists(base_path):
                if time.time() - start_time > timeout:
                    return None  # No se creó a tiempo
                time.sleep(0.1)

        return base_path
    # ---------------- CARGA Y VALIDACIÓN ----------------

    info = fetch_ticker_info(ticker)
    df = fetch_price_history(ticker, period, interval)

    if "error" in info or df.empty:
        st.error(f"No se pudo obtener la información del ticker '{ticker}'")
        st.stop()

    # ---------------- CÁLCULO DE INDICADORES ----------------

    # EMA 20
    if show_ema:
        df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()

    # EMA 200
    if show_ema:
        df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()

    # RSI 14
    if show_rsi:
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()

        rs = avg_gain / avg_loss
        df["RSI"] = 100 - (100 / (1 + rs))

    # ---------------- LAYOUT PRINCIPAL ----------------

    col1, col2 = st.columns([2, 3])

    # ----- Columna izquierda: info general -----

    with col1:
        st.subheader(f"Datos de {info['name']}")
        st.write(f"**Sector:** {info['sector']}")
        st.write(f"**Industria:** {info['industry']}")
        st.write(f"**País:** {info['country']}")
        st.write(f"**Precio actual:** ${info['price']}")
        st.write(f"**Market Cap:** {info['market_cap']:,}" if info['market_cap'] else "N/A")
        st.write(f"**P/E Ratio:** {info['pe_ratio']}")
        st.write(f"**P/B Ratio:** {info['pb_ratio']}")
        st.write(f"**Dividend Yield:** {round(info['dividend_yield'], 2)}%" if info['dividend_yield'] else "N/A")

        st.markdown("---")
        st.write(info["description"][:500] + "...")

    # ----- Columna derecha: gráfico -----

    with col2:
        st.markdown("<h3 style='text-align: center;'>Gráfico Price-Action</h3>", unsafe_allow_html=True)

        # Preprocesamiento robusto
        df.index = pd.to_datetime(df.index, errors='coerce')
        df = df[df.index.notna()]

        required_cols = ["Open", "High", "Low", "Close"]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            st.error(f"Faltan columnas necesarias en los datos: {', '.join(missing_cols)}")
            st.stop()

        df.index = pd.to_datetime(df.index, errors='coerce')
        df = df[df.index.notna()]

    # Asegurarse de que existen todas las columnas necesarias
        required_cols = ["Open", "High", "Low", "Close"]
        df_cols = df.columns.tolist()
        valid_cols = [col for col in required_cols if col in df_cols]

        if len(valid_cols) < 4:
            st.error(f"Faltan columnas necesarias para el gráfico: {', '.join(set(required_cols) - set(valid_cols))}")
            st.stop()

    # Asegurarse de que esas columnas no estén vacías o completamente nulas
        if df[valid_cols].isnull().all().any():
            st.error("Algunas columnas necesarias están completamente vacías.")
            st.stop()

    # Finalmente: eliminar filas con NaNs (pero solo si las columnas existen y tienen datos)
        df = df.dropna(subset=valid_cols)

        fig = go.Figure()

        # 1. Candlestick (primero para que quede de fondo)
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Precio",
            increasing_line_color="lime",
            decreasing_line_color="red",
            showlegend=True
        ))

        # 2. EMA 20
        if show_ema and "EMA20" in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df["EMA20"],
                line=dict(color="deepskyblue", width=1.5),
                name="EMA 20"
            ))

        #2.0 EMA 200
        if show_ema and "EMA200" in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df["EMA200"],
                line=dict(color="orange", width=1.5),
                name="EMA 200"
            ))

        # 3. Volumen como segundo eje
        if show_volume and "Volume" in df.columns:
            fig.add_trace(go.Bar(
                x=df.index,
                y=df["Volume"],
                name="Volumen",
                yaxis="y2",
                marker=dict(color="gray", opacity=0.3)
            ))
            fig.update_layout(yaxis2=dict(
                overlaying="y",
                side="right",
                showgrid=False,
                title="Volumen"
            ))

        # Configuración visual
        fig.update_layout(
            template="plotly_dark",
            xaxis_title="Fecha",
            yaxis_title="Precio",
            margin=dict(t=20, l=20, r=20, b=20),
            xaxis_rangeslider_visible=False,
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)

        # RSI abajo
        if show_rsi and "RSI" in df.columns:
            st.markdown("<h3 style='text-align: center;'>RSI</h3>", unsafe_allow_html=True)
            st.line_chart(df["RSI"])

    # ---------------- BALANCE 10-K / 10-Q ----------------

    with st.spinner("📥 Descargando y procesando balance desde SEC..."):
        balance_path = fetch_balance_path(ticker)

    st.subheader("📑 Último balance financiero (10-K)")

    with open(balance_path, "rb") as f:
        st.download_button(
            label="🔍 Abrir balance en nueva pestaña",
            data=f,
            file_name="balance.html",
            mime="text/html"
        )


    

if tab == "Terminal":
    render_equity_terminal()
if tab == "Options Workstation":
    render_options_workstation()