import pandas as pd
import os

CSV_FILE = "nse500.csv"

def load_nse500():
    if not os.path.exists(CSV_FILE):
        return []

    df = pd.read_csv(CSV_FILE)
    symbols = (
        df["Symbol"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
        .unique()
        .tolist()
    )

    return [s + ".NS" if not s.endswith(".NS") else s for s in symbols]

NSE500 = load_nse500()