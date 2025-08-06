import math
from scipy.stats import norm
from data_fetch import fetch_interest_rate

def black_scholes(S, K, T, sigma, option_type):
    r = fetch_interest_rate()
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    if option_type == "Calls":
        price = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    elif option_type == "Puts":
        price = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    else:
        raise ValueError("option_type debe ser 'call' o 'put'")
    
    return price
