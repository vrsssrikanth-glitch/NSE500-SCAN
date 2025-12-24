import numpy as np
import pandas as pd
from indicators import compute_rsi

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]
def technical_summary(df):
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    # --- ATR ---
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = float(tr.rolling(14).mean().iloc[-1])

    # --- EMA (FORCED SCALARS) ---
    ema50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
    ema200 = float(close.ewm(span=200, adjust=False).mean().iloc[-1])

    trend = "Bullish" if ema50 > ema200 else "Bearish"

    return {
        "LTP": float(round(close.iloc[-1], 2)),
        "RSI(14)": float(round(rsi(close), 2)),
        "EMA50": float(round(ema50, 2)),
        "EMA200": float(round(ema200, 2)),
        "ATR": float(round(atr, 2)),
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




