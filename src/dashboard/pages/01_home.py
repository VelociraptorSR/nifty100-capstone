"""Home Screen — Sprint 4, Day 23."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

from src.dashboard.utils.db import get_companies, get_sectors

st.title("Home — Nifty 100 Overview")

DB_PATH = "data/nifty100.db"


@st.cache_data(ttl=600)
def get_home_metrics(year):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    df = pd.read_sql(
        "SELECT * FROM financial_ratios WHERE year = ?",
        conn, params=(year,)
    )
    mc = pd.read_sql(
        "SELECT company_id, pe_ratio FROM market_cap WHERE year = ?",
        conn, params=(int(year[:4]),)
    )
    conn.close()
    return df, mc


years = [f"{y}-03" for y in range(2019, 2025)]
selected_year = st.sidebar.selectbox("Select Year", years, index=len(years) - 1)

ratios, market_cap = get_home_metrics(selected_year)

if ratios.empty:
    st.warning(f"No data available for {selected_year}. Try a different year.")
else:
    avg_roe = ratios["return_on_equity_pct"].mean()
    median_de = ratios["debt_to_equity"].median()
    median_pe = market_cap["pe_ratio"].median() if not market_cap.empty else None
    total_companies = ratios["company_id"].nunique()
    median_rev_cagr = ratios["revenue_cagr_5yr"].median()
    debt_free_count = (ratios["debt_to_equity"] == 0).sum()

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Average ROE", f"{avg_roe:.1f}%" if pd.notna(avg_roe) else "N/A")
    col2.metric("Median P/E", f"{median_pe:.1f}" if median_pe is not None and pd.notna(median_pe) else "N/A")
    col3.metric("Median D/E", f"{median_de:.2f}" if pd.notna(median_de) else "N/A")
    col4.metric("Total Companies", total_companies)
    col5.metric("Median Rev CAGR 5yr", f"{median_rev_cagr:.1f}%" if pd.notna(median_rev_cagr) else "N/A")
    col6.metric("Debt-Free Companies", debt_free_count)

    st.divider()

    left, right = st.columns([1, 1])

    with left:
        st.subheader("Sector Breakdown")
        st.caption("Company count by sector (static — does not vary by year)")
        sectors = get_sectors()
        sector_counts = sectors["broad_sector"].value_counts().reset_index()
        sector_counts.columns = ["broad_sector", "count"]
        fig = px.pie(sector_counts, names="broad_sector", values="count", hole=0.5)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Top 5 by Composite Quality Score")
        companies = get_companies()
        top5 = ratios.merge(companies, left_on="company_id", right_on="id", how="left")
        top5 = top5.sort_values("composite_quality_score", ascending=False).head(5)
        st.dataframe(
            top5[["company_id", "company_name", "composite_quality_score"]].rename(
                columns={"company_id": "Ticker", "company_name": "Name", "composite_quality_score": "Score"}
            ),
            hide_index=True,
        )