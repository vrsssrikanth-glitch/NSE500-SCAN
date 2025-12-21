from indicators import compute_rsi

def technical_summary(df):
    close = df["Close"]
    if hasattr(close, "columns"):
        close = close.iloc[:, 0]

    ema50 = close.ewm(span=50).mean()
    ema200 = close.ewm(span=200).mean()
    rsi = compute_rsi(close).iloc[-1]
    ltp = float(close.iloc[-1])

    trend = "Sideways"
    if ltp > ema50.iloc[-1] > ema200.iloc[-1]:
        trend = "Bullish"
    elif ltp < ema200.iloc[-1]:
        trend = "Bearish"

    return {
        "LTP": round(ltp, 2),
        "RSI(14)": round(rsi, 2),
        "EMA50": round(ema50.iloc[-1], 2),
        "EMA200": round(ema200.iloc[-1], 2),
        "Trend": trend
    }


def entry_target_exit(tech):
    ltp = tech["LTP"]

    if tech["Trend"] == "Bullish":
        entry = ltp * 0.98
        target = ltp * 1.15
        stop = ltp * 0.94
    elif tech["Trend"] == "Bearish":
        entry = ltp * 0.95
        target = ltp * 1.20
        stop = ltp * 0.90
    else:
        entry = ltp
        target = ltp * 1.10
        stop = ltp * 0.95

    return {
        "Suggested Entry": round(entry, 2),
        "Target Price": round(target, 2),
        "Stop Loss": round(stop, 2)
    }
