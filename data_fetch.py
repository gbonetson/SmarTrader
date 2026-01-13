import yfinance as yf
import pandas as pd
import requests
import streamlit as st
import time
import os
from datetime import datetime, timedelta
from balance_sheet import extract_filings

FINNHUB_API_KEY = st.secrets.get(
    "FINNHUB_API_KEY",
    os.getenv("FINNHUB_API_KEY")
)

BASE_URL = "https://finnhub.io/api/v1/stock/candle"

def fetch_ticker_info(ticker: str) -> dict:
    """
    Devuelve la info general del ticker usando yfinance.
    """
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
            "logo_url": info.get("logo_url", None),
        }
    except Exception as e:
        return {"error": str(e)}

def fetch_price_history(
    ticker: str,
    period: str = "1y",
    interval: str = "1d"
) -> pd.DataFrame:
    """
    Fetch OHLCV data from Finnhub.
    Returns empty DataFrame if anything fails.
    """

    if FINNHUB_API_KEY is None:
        return pd.DataFrame()

    # ---- interval mapping ----
    interval_map = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "1d": "D"
    }

    if interval not in interval_map:
        return pd.DataFrame()

    # ---- period → timestamps ----
    now = int(time.time())

    period_map = {
        "5d": 5,
        "1mo": 30,
        "3mo": 90,
        "6mo": 180,
        "1y": 365,
        "max": 365 * 20
    }

    days = period_map.get(period, 365)
    start = int((datetime.utcnow() - timedelta(days=days)).timestamp())

    params = {
        "symbol": ticker.upper(),
        "resolution": interval_map[interval],
        "from": start,
        "to": now,
        "token": FINNHUB_API_KEY
    }

    try:
        r = requests.get(BASE_URL, params=params, timeout=10)
        data = r.json()
    except Exception:
        return pd.DataFrame()

    # Finnhub error handling
    if data.get("s") != "ok":
        return pd.DataFrame()

    df = pd.DataFrame({
        "Datetime": pd.to_datetime(data["t"], unit="s"),
        "Open": data["o"],
        "High": data["h"],
        "Low": data["l"],
        "Close": data["c"],
        "Volume": data["v"],
    })

    df.set_index("Datetime", inplace=True)
    return df


def fetch_balance_path(ticker: str) -> str:
    """
    Devuelve el path al HTML del balance generado por el usuario.
    """
    base_path = f"./sheets/{ticker}_bs.html"
    if os.path.exists(base_path):
        return base_path 
    else:
        extract_filings(ticker, save_as=f'./sheets/{ticker}_bs.html')

def fetch_option_exp(ticker):
    expirations = yf.Ticker(ticker).options
    return expirations

def fetch_option_chain(ticker, exp):
    data = yf.Ticker(ticker).option_chain(exp)
    return data

def fetch_interest_rate():
    t_bill = yf.Ticker("^IRX")
    tasa_actual = t_bill.history(period="1d")['Close'].iloc[-1] / 100  # Convierte de % a decimal
    r = tasa_actual
    return r