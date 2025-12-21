import yfinance as yf

def get_price_data(symbol, period="2Y"):
    try:
        df = yf.download(
            symbol,
            period=period,
            auto_adjust=True,
            progress=False
        )
        if df is None or df.empty:
            return None
        return df
    except:
        return None


def get_fundamental_info(symbol):
    try:
        return yf.Ticker(symbol).info
    except:
        return {}