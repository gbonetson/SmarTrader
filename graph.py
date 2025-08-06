import yfinance as yf
import pandas as pd
import mplfinance as mpf

def get_stock_data(ticker):
    df = yf.download(ticker, period="3mo", interval="1d")

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

def graph_plot(df, ticker):
    mpf.plot(
        df.tail(200),
        type='candle',
        style='yahoo',
        title=f"{ticker} - Últimas 40 velas",
        volume=True,
        show_nontrading=True,
        figratio=(10,5),
        mav=(20, 5)
    )

if __name__ == "__main__":
    t = input("Ticker: ").upper()
    data = get_stock_data(t)
    graph_plot(data, t)
