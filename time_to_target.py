import math
from typing import Optional, Dict, Any

import numpy as np
import pandas as pd

from data_loader import get_price_data


def _ensure_df(df: Optional[pd.DataFrame], symbol: Optional[str], lookback: Optional[int] = None) -> pd.DataFrame:
    """
    Helper to obtain a dataframe either from the provided df or by loading via symbol.
    If lookback is provided it will tail() the dataframe to that length.
    """
    if df is None:
        if not symbol:
            raise ValueError("Either `df` or `symbol` must be provided.")
        df = get_price_data(symbol)
    if not isinstance(df, pd.DataFrame):
        raise ValueError("`df` must be a pandas DataFrame.")
    df = df.copy()
    if lookback:
        df = df.tail(lookback)
    df = df.sort_index()  # ensure chronological order
    return df


def estimate_time_to_target_empirical(df: Optional[pd.DataFrame] = None,
                                      symbol: Optional[str] = None,
                                      target_mult: float = 2.0,
                                      lookback: int = 250) -> Optional[Dict[str, Any]]:
    """
    Empirical estimation using historical bullish regimes.

    Parameters:
    - df: price dataframe (must contain at least 'High','Low','Close' columns) OR
    - symbol: symbol used to load data if df is not provided
    - target_mult: multiplies ATR to compute the target (entry + target_mult * ATR)
    - lookback: number of most recent rows to consider

    Returns:
    - dict with median/min/max days and sample size, or None if no matches.
    """
    df = _ensure_df(df, symbol, lookback=lookback)

    # Need at minimum enough rows to compute indicators
    if len(df) < 30:
        return None

    # Indicators
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()

    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean().replace(0, np.nan)  # avoid division by zero

    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    tr1 = df["High"] - df["Low"]
    tr2 = (df["High"] - df["Close"].shift()).abs()
    tr3 = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(14).mean()

    times = []

    # We'll iterate by positional index because we want to measure days forward by position
    n = len(df)
    max_lookahead = 30

    for pos in range(n - max_lookahead):
        row = df.iloc[pos]

        # Skip if required indicators are missing for this row
        if pd.isna(row.get("ATR")) or pd.isna(row.get("EMA50")) or pd.isna(row.get("EMA200")) or pd.isna(row.get("RSI")):
            continue

        # Bullish regime criteria
        if (
            (row["Close"] > row["EMA50"] > row["EMA200"])
            and (row["RSI"] > 55)
        ):
            entry = float(row["Close"])
            target = entry + target_mult * float(row["ATR"])

            future = df.iloc[pos + 1: pos + 1 + max_lookahead]

            hit = future[future["High"] >= target]

            if not hit.empty:
                # compute days as positional difference (1 == next trading day)
                try:
                    hit_idx = hit.index[0]
                    days = df.index.get_loc(hit_idx) - df.index.get_loc(row.name)
                except Exception:
                    # fallback to positional compute
                    hit_pos = hit.index[0]
                    days = 1
                if days >= 1:
                    times.append(int(days))

    if not times:
        return None

    return {
        "median_days": int(np.median(times)),
        "min_days": int(np.min(times)),
        "max_days": int(np.max(times)),
        "sample_size": len(times)
    }


def estimate_time_to_target_trend_based(df: Optional[pd.DataFrame] = None,
                                        entry: Optional[float] = None,
                                        target: Optional[float] = None,
                                        symbol: Optional[str] = None,
                                        lookback: int = 60) -> Optional[int]:
    """
    Trend-speed-based estimation using recent market regime.

    Parameters:
    - df or symbol: price data or symbol to load
    - entry: entry price (required)
    - target: target price (required)
    - lookback: number of most recent rows to consider

    Returns:
    - estimated days (int) between 2 and 30 inclusive, or None if cannot estimate
    """
    if entry is None or target is None:
        raise ValueError("Both `entry` and `target` must be provided for trend-based estimation.")

    df = _ensure_df(df, symbol, lookback=lookback)

    # Need enough data to compute EMA50 and ATR and compute slope over a window
    min_rows_required = 50
    if len(df) < min_rows_required:
        # relax calculation if we have at least 15 rows
        if len(df) < 15:
            return None

    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()

    tr1 = df["High"] - df["Low"]
    tr2 = (df["High"] - df["Close"].shift()).abs()
    tr3 = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(14).mean()

    latest_atr = df["ATR"].iloc[-1]
    if pd.isna(latest_atr) or latest_atr <= 0:
        return None

    # Trend velocity: use changes over last 10 bars if available
    lookback_for_slope = min(10, len(df) - 1)
    if lookback_for_slope < 2:
        return None

    ema_diff = df["EMA50"].iloc[-1] - df["EMA50"].iloc[-1 - lookback_for_slope]
    ema_slope = ema_diff / lookback_for_slope

    momentum = (df["Close"].iloc[-1] - df["Close"].iloc[-1 - lookback_for_slope]) / lookback_for_slope

    # trend_speed is measured in ATRs per day (approx)
    trend_speed = (ema_slope + momentum) / latest_atr

    # If trend_speed is non-positive, can't estimate a positive time-to-target
    if trend_speed <= 0:
        return None

    distance = abs(target - entry)

    # trend_speed * latest_atr gives price movement per day (approx)
    price_per_day = trend_speed * latest_atr
    if price_per_day <= 0:
        return None

    est_days = int(math.ceil(distance / price_per_day))

    # constrain to reasonable bounds
    est_days = max(2, min(est_days, 30))
    return est_days


def estimate_final_days_to_target(df: Optional[pd.DataFrame] = None,
                                  entry: Optional[float] = None,
                                  target: Optional[float] = None,
                                  symbol: Optional[str] = None,
                                  target_mult: float = 2.0) -> Optional[Dict[str, Any]]:
    """
    Combines empirical and trend-based estimates.

    Parameters:
    - df or symbol: price data or symbol to load
    - entry, target: required for trend-based estimate
    - target_mult: passed to empirical estimator (entry + target_mult * ATR)

    Returns:
    - dict with combined and component estimates, or None if no estimate possible
    """
    # For empirical we only need price series; allow symbol to be used
    empirical = None
    try:
        empirical = estimate_time_to_target_empirical(df=df, symbol=symbol, target_mult=target_mult)
    except Exception:
        empirical = None

    trend_based = None
    try:
        # If df is None but symbol provided, trend-based will load it
        if entry is not None and target is not None:
            trend_based = estimate_time_to_target_trend_based(df=df, entry=entry, target=target, symbol=symbol)
    except Exception:
        trend_based = None

    if empirical and trend_based:
        final_days = int(round(0.6 * empirical["median_days"] + 0.4 * trend_based))
    elif trend_based:
        final_days = int(trend_based)
    elif empirical:
        final_days = int(empirical["median_days"])
    else:
        return None

    return {
        "final_estimated_days": final_days,
        "trend_based_days": trend_based,
        "historical_median_days": empirical["median_days"] if empirical else None,
        "historical_sample_size": empirical["sample_size"] if empirical else 0
    }
