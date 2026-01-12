import yfinance as yf
import pandas as pd
import requests
import os
from balance_sheet import extract_filings

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


def fetch_price_history(ticker, period="1y", interval="1d"):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    })

    try:
        t = yf.Ticker(ticker, session=session)
        df = t.history(
            period=period,
            interval=interval,
            auto_adjust=False
        )
    except Exception as e:
        return pd.DataFrame()

    if df is None or df.empty:
        return pd.DataFrame()

    REQUIRED = {"Open", "High", "Low", "Close", "Volume"}
    if not REQUIRED.issubset(df.columns):
        return pd.DataFrame()

    return df.reset_index()



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