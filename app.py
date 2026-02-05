import streamlit as st
import pandas as pd
from io import BytesIO

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Smart Money Bulk Deal Dashboard-By Nyra & Eia",
    layout="wide"
)

st.title("📊 Smart Money Bulk Deal Dashboard-By Nyra & Eia")
st.caption("Educational market intelligence tool")

# ======================================================
# HELPER FUNCTIONS
# ======================================================
def calculate_probability_score(row, max_qty):
    qty_score = (row["Net_Accumulation_Qty"] / max_qty) * 60 if max_qty > 0 else 0

    conviction_score = (row["Buy_Days"] - row["Sell_Days"]) * 10
    conviction_score = max(min(conviction_score, 30), 0)

    distribution_penalty = -row["Sell_Days"] * 5
    distribution_penalty = max(distribution_penalty, -20)

    score = qty_score + conviction_score + distribution_penalty
    return round(max(min(score, 100), 0), 1)


def df_to_csv(df):
    return df.to_csv(index=False).encode("utf-8")


def df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Report")
    return output.getvalue()


# ======================================================
# LOAD & CLEAN DATA
# ======================================================
try:
    DATA_URL = "https://raw.githubusercontent.com/aiearyn/smart-money-bulk-dashboard/main/bulk_deals.csv"
    df = pd.read_csv(DATA_URL)
except Exception:
    df = pd.read_csv("bulk_deals.csv")


df.columns = df.columns.str.strip()

BUY_SELL_COL = "Buy / Sell"
QTY_COL = "Quantity Traded"
SYMBOL_COL = "Symbol"
DATE_COL = "Date"

df[QTY_COL] = (
    df[QTY_COL]
    .astype(str)
    .str.replace(",", "", regex=False)
    .astype(int)
)

df["Signed_Qty"] = df.apply(
    lambda r: r[QTY_COL]
    if r[BUY_SELL_COL].strip().upper() == "BUY"
    else -r[QTY_COL],
    axis=1
)

# ======================================================
# AGGREGATIONS
# ======================================================
net_qty = (
    df.groupby(SYMBOL_COL)["Signed_Qty"]
    .sum()
    .reset_index()
    .rename(columns={"Signed_Qty": "Net_Accumulation_Qty"})
)

buy_days = (
    df[df[BUY_SELL_COL].str.upper() == "BUY"]
    .groupby(SYMBOL_COL)[DATE_COL]
    .nunique()
    .reset_index()
    .rename(columns={DATE_COL: "Buy_Days"})
)

sell_days = (
    df[df[BUY_SELL_COL].str.upper() == "SELL"]
    .groupby(SYMBOL_COL)[DATE_COL]
    .nunique()
    .reset_index()
    .rename(columns={DATE_COL: "Sell_Days"})
)

# ======================================================
# FINAL REPORT CREATION
# ======================================================
report = (
    net_qty
    .merge(buy_days, on=SYMBOL_COL, how="left")
    .merge(sell_days, on=SYMBOL_COL, how="left")
    .fillna(0)
)

report["Market_Bias"] = report.apply(
    lambda r: "Accumulation"
    if r["Buy_Days"] > r["Sell_Days"]
    else "Distribution"
    if r["Sell_Days"] > r["Buy_Days"]
    else "Neutral",
    axis=1
)

max_qty = report["Net_Accumulation_Qty"].max()

report["Probability_Score"] = report.apply(
    lambda r: calculate_probability_score(r, max_qty),
    axis=1
)

report = report.sort_values("Probability_Score", ascending=False)

# ======================================================
# SIDEBAR FILTERS (ALL VARIABLES DEFINED HERE)
# ======================================================
st.sidebar.header("🔍 Filters")

min_buy_days = st.sidebar.slider(
    "Minimum Buy Days",
    0,
    int(report["Buy_Days"].max()),
    1
)

show_only_buyers = st.sidebar.checkbox(
    "Show only Net Buyers",
    value=True
)

search_text = st.sidebar.text_input(
    "🔎 Search Symbol",
    placeholder="Type stock symbol (e.g. TATA, INFRA)"
)

# ======================================================
# APPLY FILTERS
# ======================================================
filtered = report.copy()

if show_only_buyers:
    filtered = filtered[filtered["Net_Accumulation_Qty"] > 0]

filtered = filtered[filtered["Buy_Days"] >= min_buy_days]

if search_text:
    filtered = filtered[
        filtered[SYMBOL_COL].str.contains(search_text, case=False, na=False)
    ]

# ======================================================
# QUICK VIEW BUTTONS
# ======================================================
st.subheader("⚡ Quick View")

c1, c2, c3 = st.columns(3)

with c1:
    top10 = st.button("Top 10")
with c2:
    top20 = st.button("Top 20")
with c3:
    show_all = st.button("All Stocks")

display_df = filtered.copy()

if top10:
    display_df = filtered.head(10)
elif top20:
    display_df = filtered.head(20)

# ======================================================
# DATA TABLE
# ======================================================
st.subheader("📋 Accumulation & Distribution Table")

st.dataframe(
    display_df,
    width="stretch"
)

# ======================================================
# BAR CHART
# ======================================================
st.subheader("📊 Top Accumulation Chart")

top_n = st.slider("Top N Stocks", 5, 30, 10)

chart_data = (
    display_df
    .head(top_n)
    .set_index(SYMBOL_COL)["Net_Accumulation_Qty"]
)

st.bar_chart(chart_data)

# ======================================================
# DOWNLOAD SECTION
# ======================================================
st.subheader("⬇ Download Report")

st.download_button(
    "📥 Download CSV",
    df_to_csv(display_df),
    "bulk_deal_report.csv",
    "text/csv"
)

st.download_button(
    "📥 Download Excel",
    df_to_excel(display_df),
    "bulk_deal_report.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.caption("⚠ This is NOT investment advice. Data is for study & research only.")





