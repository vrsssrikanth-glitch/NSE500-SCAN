import streamlit as st
from universe import NSE500
from data_loader import get_price_data, get_fundamental_info
from fundamentals import fundamental_summary
from technicals import technical_summary, entry_target_exit

st.set_page_config(page_title="Personal Stock Scanner", layout="wide")

st.title("📊 Personal NSE Stock Scanner (Offline)")

st.info(
    "This tool is for personal analysis only. "
    "It runs on historical data and works even during market closed hours."
)

# --------------------------------------------------
# USER INTEREST STOCK
# --------------------------------------------------

st.header("🔍 Analyze Your Stock")

user_stock = st.text_input(
    "Enter NSE stock symbol (e.g., TATAMOTORS, INFY, RELIANCE):"
)

if user_stock:
    symbol = user_stock.strip().upper() + ".NS"

    df = get_price_data(symbol)
    if df is None:
        st.error("No data found for this stock.")
    else:
        info = get_fundamental_info(symbol)

        tech = technical_summary(df)
        funda = fundamental_summary(info)
        trade = entry_target_exit(tech)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("📈 Technical View")
            st.json(tech)

        with col2:
            st.subheader("🏦 Fundamental View")
            st.json(funda)
            
        with col3:
            st.subheader("🎯 Trade Levels & Time Estimates")

            st.metric("Current Price (LTP)", f"₹{tech['LTP']}")
            st.metric("Entry Price", f"₹{trade['Entry Price']}")
            st.metric("Target Price", f"₹{trade['Target Price']}")
            st.metric("Stop Loss", f"₹{trade['Stop Loss']}")

            st.info(
              f"⏳ Estimated **{trade['Estimated Working Days to Entry']} working days** "
              f"to reach Entry price"
             )
            st.success(
              f"🎯 After entry, estimated **{trade['Estimated Working Days to Target']} "
              f"working days** to reach Target"
             )

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





