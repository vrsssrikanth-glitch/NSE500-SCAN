import numpy as np

def estimate_time_to_target(df, atr, target_mult=3, lookback=250):
    df = df.copy()
    df = df.tail(lookback)

    times = []

    for i in range(len(df)-20):
        row = df.iloc[i]

        # Similar bullish condition
        if row["Close"] > row["EMA50"] > row["EMA200"] and row["RSI"] > 55:
            entry = row["Close"]
            target = entry + (atr * target_mult)

            future = df.iloc[i+1:i+31]  # next 1 month

            hit = future[future["High"] >= target]

            if not hit.empty:
                days = hit.index[0] - row.name
                times.append(days.days)

    if not times:
        return None

    return {
        "median_days": int(np.median(times)),
        "min_days": int(min(times)),
        "max_days": int(max(times))
    }
