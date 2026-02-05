import streamlit as st
import pandas as pd
import os

# ===============================
# APP CONFIG
# ===============================
st.set_page_config(
    page_title="Smart Money Bulk Deal Dashboard",
    layout="wide"
)

# ===============================
# CSV COLUMN DEFINITIONS (EXACT)
# ===============================
DATE_COL = "Date "
SYMBOL_COL = "Symbol "
SECURITY_COL = "Security Name "
CLIENT_COL = "Client Name "
BUY_SELL_COL = "Buy / Sell "
QTY_COL = "Quantity Traded "
PRICE_COL = "Trade Price / Wght. Avg. Price "
REMARKS_COL = "Remarks "

# ===============================
# DATA LOADING
# ===============================
DATA_FILE = "data/bulk_deals.csv"
HISTORY_FILE = "data/bulk_deals_history.csv"

@st.cache_data
def load_csv(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

df = load_csv(DATA_FILE)
df_history = load_csv(HISTORY_FILE)

# ===============================
# BASIC VALIDATION
# ===============================
if df.empty:
    st.error("Main bulk deals CSV not found or empty.")
    st.stop()

# ===============================
# PREPROCESSING
# ===============================
df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
df[QTY_COL] = pd.to_numeric(df[QTY_COL], errors="coerce")

df["Signed_Qty"] = df.apply(
    lambda r: r[QTY_COL] if str(r[BUY_SELL_COL]).upper() == "BUY" else -r[QTY_COL],
    axis=1
)

# ===============================
# UI
# ===============================
st.title("📊 Smart Money Bulk Deal Dashboard – By Nyra & Eia")
st.caption("Educational market intelligence tool")

st.subheader("Raw Bulk Deal Data")
st.dataframe(df.head(50), use_container_width=True)

# ===============================
# SIMPLE INSIGHT
# ===============================
accumulation = (
    df.groupby(SYMBOL_COL)["Signed_Qty"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

st.subheader("Top Accumulation Stocks")
st.dataframe(accumulation.head(20), use_container_width=True)
