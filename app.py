import streamlit as st
import pandas as pd

import streamlit as st
from universe import NSE500
from data_loader import get_price_data, get_fundamental_info
from fundamentals import fundamental_summary
from technicals import technical_summary, entry_target_exit
from time_to_target import estimate_time_to_target

# ==============================
# PAGE CONFIG & TITLE
# ==============================
st.set_page_config(page_title="Personal Stock Scanner", layout="wide")
st.title("📊 Personal Stock Scanner (Technical + Volatility)")
st.caption("For personal analytical use only. No financial advice.")

# ==============================
# UI CONTROLS (DEFINE FIRST)
# ==============================
mode = st.radio(
    "Select Mode",
    ["Single Stock", "NSE500 Scan"],
    horizontal=True
)

period = st.selectbox(
    "Select Analysis Period",
    ["6mo", "1y", "2y", "5y"],
    index=2
)

trade_type = st.selectbox(
    "Trade Style",
    ["short", "positional"],
    index=1
)

st.divider()

# ==============================
# SINGLE STOCK MODE
# ==============================
if mode == "Single Stock":

    symbol = st.text_input("Enter Stock Symbol (e.g. NATIONALUM.NS)")

    if st.button("Analyze"):

        if symbol.strip() == "":
            st.warning("Please enter a valid stock symbol.")
        else:
            df = get_price_data(symbol, period)

            if df is None or df.empty:
                st.error("No data found for this symbol.")
            else:
                # ---- Calculations ----
                df = compute_indicators(df)
                atr_series = compute_atr(df)

                if atr_series.isna().all():
                    st.error("Not enough data to compute ATR.")
                else:
                    atr = atr_series.iloc[-1]
                    ltp = df["Close"].iloc[-1]

                    entry, target, stop = calculate_trade_levels(
                        ltp, atr, trade_type
                    )

                    time_info = estimate_time_to_target(df, atr)

                    # ---- Display ----
                    st.subheader(f"📌 {symbol}")
                    st.write("**Trend:**", trend_label(df))
                    st.write("**Last Traded Price (LTP):** ₹", round(ltp, 2))
                    st.write("**ATR (Volatility):**", round(atr, 2))

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Entry", entry)
                    col2.metric("Target", target)
                    col3.metric("Stop Loss", stop)

                    if time_info:
                        st.subheader("⏱ Historical Time-to-Target")
                        st.write(
                            f"Typical: {time_info['median_days']} trading days"
                        )
                        st.write(
                            f"Fastest: {time_info['min_days']} days"
                        )
                        st.write(
                            f"Slowest: {time_info['max_days']} days"
                        )
                        st.caption(
                            "Based on historical tendencies only. Not a prediction."
                        )

                    st.line_chart(df["Close"])

# ==============================
# NSE500 SCAN MODE
# ==============================
else:
    uploaded = st.file_uploader(
        "Upload NSE500 CSV (must contain column: Symbol)",
        type=["csv"]
    )

    if uploaded and st.button("Run Scan"):
        try:
            symbols = pd.read_csv(uploaded)["Symbol"].dropna().unique().tolist()
        except Exception:
            st.error("CSV must contain a column named 'Symbol'.")
            st.stop()

        results = []

        for sym in symbols:
            df = load_stock(sym, period)

            if df is None or len(df) < 200:
                continue

            df = compute_indicators(df)
            score = bullish_score(df)

            if score >= 3:
                atr_series = compute_atr(df)
                if atr_series.isna().all():
                    continue

                atr = atr_series.iloc[-1]
                ltp = df["Close"].iloc[-1]

                entry, target, stop = calculate_trade_levels(
                    ltp, atr, trade_type
                )

                results.append({
                    "Stock": sym,
                    "LTP": round(ltp, 2),
                    "Trend": trend_label(df),
                    "Entry": entry,
                    "Target": target,
                    "Stop": stop
                })

        if results:
            st.success(f"Found {len(results)} bullish candidates")
            st.dataframe(pd.DataFrame(results))
        else:
            st.warning("No bullish stocks found under current conditions.")


