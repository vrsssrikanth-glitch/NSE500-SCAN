import streamlit as st
from universe import NSE500
from data_loader import get_price_data, get_fundamental_info
from fundamentals import fundamental_summary
from technicals import technical_summary, entry_target_exit
from time_to_target import estimate_time_to_target

st.set_page_config(page_title="Personal Stock Scanner", layout="wide")

st.title("📊 Personal NSE Stock Scanner (Offline)")

st.info(
    "This tool is for personal analysis only. "
    "It runs on historical data and works even during market closed hours."
)


# --------------------------------------------------
# USER INTEREST STOCK
# --------------------------------------------------

if mode == "Single Stock":
    symbol = st.text_input("Enter Stock Symbol (e.g. NATIONALUM.NS)")

    if st.button("Analyze"):
        if symbol.strip() == "":
            st.warning("Please enter a stock symbol")
        else:
            df = load_stock(symbol, period)

            if df is None:
                st.error("No data found")
            else:
                df = compute_indicators(df)
                atr = compute_atr(df).iloc[-1]

                ltp = df["Close"].iloc[-1]
                entry, target, stop = calculate_trade_levels(ltp, atr, trade_type)

                time_info = estimate_time_to_target(df, atr)

                st.subheader(f"📌 {symbol}")
                st.write("**Trend:**", trend_label(df))
                st.write("**LTP:** ₹", round(ltp,2))

                col1, col2, col3 = st.columns(3)
                col1.metric("Entry", entry)
                col2.metric("Target", target)
                col3.metric("Stop Loss", stop)

                if time_info:
                    st.subheader("⏱ Historical Time-to-Target")
                    st.write(f"Typical: {time_info['median_days']} trading days")
                    st.write(f"Fastest: {time_info['min_days']} days")
                    st.write(f"Slowest: {time_info['max_days']} days")
                    st.caption("Based on historical tendencies, not a prediction.")
# --------------------------------------------------
# BEST STOCK SCAN
# --------------------------------------------------

st.header("⭐ Best Stock from NSE 500 (< ₹500)")

if st.button("Run Scan"):
    best_bull = None
    best_score = -1

    for sym in NSE500:
        df = get_price_data(sym)
        if df is None or len(df) < 220:
            continue

        tech = technical_summary(df)
        if tech["LTP"] > 500 or tech["Trend"] != "Bullish":
            continue

        info = get_fundamental_info(sym)
        funda = fundamental_summary(info)
        if not funda["Fundamental Pass"]:
            continue

        score = funda["ROE (%)"] + tech["RSI(14)"]
        if score > best_score:
            best_score = score
            best_bull = sym

    if best_bull:
        st.success(f"📈 Best Bullish Stock (<₹500): {best_bull}")
    else:
        st.warning("No suitable bullish stock found.")




