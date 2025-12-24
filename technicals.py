import numpy as np
import pandas as pd
from indicators import compute_rsi

import pandas as pd
import numpy as np

def technical_summary(df):
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    # --- ATR calculation ---
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr_series = tr.rolling(window=14).mean()
    atr = atr_series.iloc[-1]

    # --- EMA calculation (SCALAR ONLY) ---
    ema50_series = close.ewm(span=50, adjust=False).mean()
    ema200_series = close.ewm(span=200, adjust=False).mean()

    ema50 = ema50_series.iloc[-1]
    ema200 = ema200_series.iloc[-1]

    # --- Trend decision (scalar comparison) ---
    trend = "Bullish" if ema50 > ema200 else "Bearish"

    return {
        "LTP": round(close.iloc[-1], 2),
        "RSI(14)": round(rsi(close), 2),
        "EMA50": round(ema50, 2),
        "EMA200": round(ema200, 2),
        "ATR": round(atr, 2),
        "Trend": trend
    }

def entry_target_exit(tech):
    """
    Calculates Entry, Target, Stoploss and
    estimated working days to reach Entry & Target (ATR-based)
    """

    ltp = tech["LTP"]
    atr = tech.get("ATR", None)

    if atr is None or atr <= 0:
        return {
            "Entry Price": ltp,
            "Target Price": None,
            "Stop Loss": None,
            "Estimated Working Days to Entry": None,
            "Estimated Working Days to Target": None
        }

    # Strategy logic
    if tech["Trend"] == "Bullish":
        entry = round(ltp - 0.5 * atr, 2)     # pullback entry
        target = round(entry + 2 * atr, 2)
        stoploss = round(entry - atr, 2)
    else:
        entry = round(ltp + 0.5 * atr, 2)
        target = round(entry - 2 * atr, 2)
        stoploss = round(entry + atr, 2)

    days_to_entry = int(np.ceil(abs(entry - ltp) / atr))
    days_to_target = int(np.ceil(abs(target - entry) / atr))

    return {
        "LTP": round(ltp, 2),
        "Entry Price": entry,
        "Target Price": target,
        "Stop Loss": stoploss,
        "ATR": round(atr, 2),
        "Estimated Working Days to Entry": days_to_entry,
        "Estimated Working Days to Target": days_to_target
    }


