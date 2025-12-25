import numpy as np
import pandas as pd
from data_loader import 

def estimate_time_to_target_empirical(df= get_price_data(symbol), target_mult=2, lookback=250):
    """
    Empirical estimation using historical bullish regimes
    """

    df = df.copy().tail(lookback)

    # Indicators
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()

    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + rs))

    tr1 = df["High"] - df["Low"]
    tr2 = (df["High"] - df["Close"].shift()).abs()
    tr3 = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(14).mean()

    times = []

    for i in range(len(df) - 30):
        row = df.iloc[i]

        if (
            row["Close"] > row["EMA50"] > row["EMA200"]
            and row["RSI"] > 55
            and not np.isnan(row["ATR"])
        ):
            entry = row["Close"]
            target = entry + target_mult * row["ATR"]

            future = df.iloc[i + 1 : i + 31]

            hit = future[future["High"] >= target]

            if not hit.empty:
                days = future.index.get_loc(hit.index[0]) + 1
                times.append(days)

    if not times:
        return None

    return {
        "median_days": int(np.median(times)),
        "min_days": int(np.min(times)),
        "max_days": int(np.max(times)),
        "sample_size": len(times)
    }

def estimate_time_to_target_trend_based(df, entry, target, lookback=60):
    """
    Trend-speed-based estimation using recent market regime
    """

    df = df.copy().tail(lookback)

    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()

    tr1 = df["High"] - df["Low"]
    tr2 = (df["High"] - df["Close"].shift()).abs()
    tr3 = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(14).mean()

    if df["ATR"].iloc[-1] <= 0 or np.isnan(df["ATR"].iloc[-1]):
        return None

    # Trend velocity
    ema_slope = (df["EMA50"].iloc[-1] - df["EMA50"].iloc[-10]) / 10
    momentum = (df["Close"].iloc[-1] - df["Close"].iloc[-10]) / 10

    trend_speed = (ema_slope + momentum) / df["ATR"].iloc[-1]

    if trend_speed <= 0:
        return None

    distance = abs(target - entry)

    est_days = int(np.ceil(distance / (trend_speed * df["ATR"].iloc[-1])))

    return max(2, min(est_days, 30))

def estimate_final_days_to_target(df, entry, target):
    """
    Combines empirical and trend-based estimates
    """

    empirical = estimate_time_to_target_empirical(df)
    trend_based = estimate_time_to_target_trend_based(df, entry, target)

    if empirical and trend_based:
        final_days = int(
            0.6 * empirical["median_days"] + 0.4 * trend_based
        )
    elif trend_based:
        final_days = trend_based
    elif empirical:
        final_days = empirical["median_days"]
    else:
        return None

    return {
        "final_estimated_days": final_days,
        "trend_based_days": trend_based,
        "historical_median_days": empirical["median_days"] if empirical else None,
        "historical_sample_size": empirical["sample_size"] if empirical else 0
    }
