import requests
import numpy as np
import pandas as pd

class FMPError(Exception):
    pass

def _get_json(url):
    r = requests.get(url, timeout=15)
    if not r.ok:
        raise FMPError(f"HTTP {r.status_code} en {url}")
    try:
        return r.json()
    except Exception as e:
        raise FMPError(f"No pude parsear JSON de {url}: {e}")

def _get_shares_outstanding(symbol, api_key):

    url_quote = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={api_key}"
    data = _get_json(url_quote)
    if isinstance(data, list) and data:
        so = data[0].get("sharesOutstanding")
        if so and so > 0:
            return int(so)

    raise FMPError("No pude obtener sharesOutstanding desde FMP (profile/key-metrics/shares_float devolvieron vacío).")

def _get_net_debt(symbol, api_key):
    # Balance más reciente
    url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{symbol}?period=annual&limit=1&apikey={api_key}"
    data = _get_json(url)
    if not (isinstance(data, list) and data):
        return None  # sin datos

    row = data[0]
    # FMP suele traer: totalDebt, netDebt, cashAndShortTermInvestments o cashAndCashEquivalents
    net_debt = row.get("netDebt")
    if net_debt is not None:
        return float(net_debt)

    total_debt = row.get("totalDebt")
    cash_like = row.get("cashAndShortTermInvestments")
    if cash_like is None:
        cash_like = row.get("cashAndCashEquivalents")

    if total_debt is not None and cash_like is not None:
        return float(total_debt) - float(cash_like)

    return None  # no alcanzó la info

def dcf_fmp(symbol, years_projection=5, wacc=0.08, g=0.02):
    api_key = "cQAcNfyGcNdQkQ9SRz3M287hiaek5G5d"

    """
    DCF simple con FCF histórico de FMP.
    - Proyecta FCF con crecimiento promedio histórico.
    - Descuenta con WACC.
    - Valor terminal por crecimiento perpetuo.
    - Ajusta EV -> Equity restando net debt si está disponible.
    - Divide por acciones -> valor intrínseco por acción.
    """
    if g >= wacc:
        raise ValueError("g debe ser menor que WACC para el método de perpetuidad.")

    # 1) FCF histórico
    url_cf = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{symbol}?period=annual&limit=10&apikey={api_key}"
    data_cf = _get_json(url_cf)
    if not (isinstance(data_cf, list) and data_cf):
        raise FMPError("No hay cash-flow-statement disponible.")

    df = pd.DataFrame(data_cf)
    if "freeCashFlow" not in df.columns:
        raise FMPError("El endpoint no trajo 'freeCashFlow'.")

    # Tomo últimos 5 valores anuales (más antiguos -> más nuevos)
    fcf_series = pd.to_numeric(df["freeCashFlow"], errors="coerce").dropna()
    if len(fcf_series) < 2:
        raise FMPError("Muy pocos puntos de FCF para estimar crecimiento.")

    fcf_hist = fcf_series.iloc[:5].values[::-1]  # FMP suele venir newest-first; esto invierte
    if len(fcf_hist) < 2:
        # Si solo hay 1, uso los primeros 2 disponibles sin invertir
        fcf_hist = fcf_series.iloc[:2].values[::-1]

    # Crecimientos promedio (evito dividir por 0)
    growths = []
    for i in range(len(fcf_hist)-1):
        if fcf_hist[i] != 0:
            growths.append(fcf_hist[i+1]/fcf_hist[i] - 1)
    avg_growth = np.clip(np.nanmean(growths), -0.5, 0.5) if growths else 0.05  # acoto a ±50%

    # 2) Proyección de FCF
    last_fcf = float(fcf_hist[-1])
    projections = [last_fcf * (1 + avg_growth)**i for i in range(1, years_projection+1)]

    # 3) Descuento
    discounted = [fcf / ((1 + wacc)**t) for t, fcf in enumerate(projections, start=1)]

    # 4) Valor terminal (perpetuity growth)
    tv = projections[-1] * (1 + g) / (wacc - g)
    tv_disc = tv / ((1 + wacc)**years_projection)

    # 5) Enterprise Value (asumiendo FCF ~ FCFF)
    ev = sum(discounted) + tv_disc

    # 6) Ajuste por deuda neta para Equity Value
    net_debt = _get_net_debt(symbol, api_key)
    if net_debt is not None:
        equity_value = ev - net_debt
    else:
        equity_value = ev  # fallback
        # Nota: si no hay net debt, EV≈Equity sólo si la deuda neta es ~0

    # 7) Acciones en circulación (robusto)
    shares_out = _get_shares_outstanding(symbol, api_key)
    intrinsic_per_share = equity_value / shares_out

    return {
        "symbol": symbol.upper(),
        "intrinsic_value_per_share": float(intrinsic_per_share),
        "assumptions": {
            "years_projection": years_projection,
            "wacc": wacc,
            "g": g,
            "avg_fcf_growth_used": float(avg_growth),
            "used_net_debt": None if net_debt is None else float(net_debt),
            "shares_outstanding": int(shares_out),
        }
    }
