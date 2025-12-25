import numpy as np
import pandas as pd

# --------------------------------------------------
# EMPIRICAL (HISTORICAL BEHAVIOUR BASED)
# --------------------------------------------------

def estimate_time_to_target_empirical(df, target_mult=2, lookback=250):
    df = df.copy().tail(lookback)

# 🔒 FORCE UNIQUE COLUMN NAMES (KEEP FIRST OCCURRENCE)
    df = df.loc[:, ~df.columns.duplicated(keep="first")]

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

      close  = float(df["Close"].iloc[i])
      ema50  = float(df["EMA50"].iloc[i])
      ema200 = float(df["EMA200"].iloc[i])
      rsi    = float(df["RSI"].iloc[i])
      atr    = float(df["ATR"].iloc[i])

    if (
        close > ema50
        and ema50 > ema200
        and rsi > 55
        and not np.isnan(atr)
    ):
        entry = close
        target = entry + target_mult * atr

        future = df.iloc[i + 1 : i + 31]
        hit = future[future["High"] >= target]

        if not hit.empty:
            days = (hit.index[0] - future.index[0]).days + 1
            times.append(days)
    if not times:
        return None

    return {
        "median_days": int(np.median(times)),
        "min_days": int(np.min(times)),
        "max_days": int(np.max(times)),
        "sample_size": len(times)
    }

# --------------------------------------------------
# TREND-BASED (CURRENT MARKET REGIME)
# --------------------------------------------------

def estimate_time_to_target_trend_based(df, entry, target, lookback=60):
    df = df.copy().tail(lookback)

    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()

    tr1 = df["High"] - df["Low"]
    tr2 = (df["High"] - df["Close"].shift()).abs()
    tr3 = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(14).mean()

    atr = df["ATR"].iloc[-1]
    if atr <= 0 or np.isnan(atr):
        return None

    ema50_now  = float(df["EMA50"].iloc[-1])
    ema50_prev = float(df["EMA50"].iloc[-10])
    close_now  = float(df["Close"].iloc[-1])
    close_prev = float(df["Close"].iloc[-10])

    ema_slope = (ema50_now - ema50_prev) / 10 
    momentum  = (close_now - close_prev) / 10

    trend_speed = float((ema_slope + momentum) / atr)
    if trend_speed <= 0:
        return None

    distance = abs(target - entry)
    est_days = int(np.ceil(distance / (trend_speed * atr)))

    return max(2, min(est_days, 30))

# --------------------------------------------------
# FINAL HYBRID ESTIMATE
# --------------------------------------------------

def estimate_final_days_to_target(df, entry, target):
    empirical = estimate_time_to_target_empirical(df)
    trend_based = estimate_time_to_target_trend_based(df, entry, target)

    if empirical and trend_based:
        final_days = int(0.6 * empirical["median_days"] + 0.4 * trend_based)
    elif trend_based:
        final_days = trend_based
    elif empirical:
        final_days = empirical["median_days"]
    else:
        return None

    return {
        "final_days": final_days,
        "trend_based_days": trend_based,
        "historical_median_days": empirical["median_days"] if empirical else None,
        "historical_sample_size": empirical["sample_size"] if empirical else 0
    }

def estimate_days_to_entry(df, entry, lookback=30):
    import numpy as np

    df = df.copy().tail(lookback)
    df = df.loc[:, ~df.columns.duplicated()]

    current = float(df["Close"].iloc[-1])

    if current >= entry:
        return 0

    tr1 = df["High"] - df["Low"]
    tr2 = (df["High"] - df["Close"].shift()).abs()
    tr3 = (df["Low"] - df["Close"].shift()).abs()
    tr = np.maximum.reduce([tr1, tr2, tr3])
    atr = float(tr.rolling(14).mean().iloc[-1])

    if np.isnan(atr) or atr <= 0:
        return None

    distance = entry - current
    est_days = int(np.ceil(distance / atr))

    return max(1, min(est_days, 10))
