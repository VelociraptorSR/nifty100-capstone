"""Sector Analysis Screen — Sprint 4, Day 25."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

st.title("Sector Analysis")

DB_PATH = "data/nifty100.db"


@st.cache_data(ttl=600)
def get_sector_data():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    sectors = pd.read_sql("SELECT * FROM sectors", conn)
    ratios = pd.read_sql("SELECT * FROM financial_ratios WHERE year != 'TTM'", conn)
    pl = pd.read_sql("SELECT company_id, year, sales FROM profitandloss WHERE year != 'TTM'", conn)
    mc = pd.read_sql("SELECT company_id, year, market_cap_crore FROM market_cap", conn)
    companies = pd.read_sql("SELECT id, company_name FROM companies", conn)
    conn.close()

    for df in [ratios, pl]:
        df["year_sortable"] = df["year"].astype(str).str.replace("-", "").astype(int)
        idx = df.groupby("company_id")["year_sortable"].idxmax()
        df.drop(df.index.difference(idx), inplace=True)

    mc["year_sortable"] = mc["year"]
    idx_mc = mc.groupby("company_id")["year_sortable"].idxmax()
    mc = mc.loc[idx_mc]

    merged = sectors.merge(companies, left_on="company_id", right_on="id", how="left")
    merged = merged.merge(ratios[["company_id", "return_on_equity_pct", "debt_to_equity", "return_on_capital_employed_pct"]], on="company_id", how="left")
    merged = merged.merge(pl[["company_id", "sales"]], on="company_id", how="left")
    merged = merged.merge(mc[["company_id", "market_cap_crore"]], on="company_id", how="left")
    return merged


data = get_sector_data()
sector_list = sorted(data["broad_sector"].dropna().unique())
selected_sector = st.selectbox("Select Sector", sector_list)

sector_data = data[data["broad_sector"] == selected_sector]

if sector_data.empty:
    st.warning("No data available for this sector.")
else:
    st.subheader(f"{selected_sector} — Revenue vs ROE")
    plot_data = sector_data.dropna(subset=["sales", "return_on_equity_pct", "market_cap_crore"])

    if plot_data.empty:
        st.info("Not enough data to render the bubble chart for this sector.")
    else:
        fig = px.scatter(
            plot_data, x="sales", y="return_on_equity_pct", size="market_cap_crore",
            color="sub_sector", hover_name="company_name",
            labels={"sales": "Revenue (Cr)", "return_on_equity_pct": "ROE (%)"},
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader(f"{selected_sector} — Median KPIs")
    medians = pd.DataFrame({
        "Metric": ["ROE (%)", "ROCE (%)", "D/E"],
        "Median": [
            sector_data["return_on_equity_pct"].median(),
            sector_data["return_on_capital_employed_pct"].median(),
            sector_data["debt_to_equity"].median(),
        ]
    })
    fig2 = px.bar(medians, x="Metric", y="Median")
    st.plotly_chart(fig2, use_container_width=True)