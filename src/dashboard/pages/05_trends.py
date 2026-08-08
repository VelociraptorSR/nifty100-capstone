"""Trend Analysis Screen — Sprint 4, Day 25."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3

st.title("Trend Analysis")

DB_PATH = "data/nifty100.db"


@st.cache_data(ttl=600)
def get_companies_list():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    df = pd.read_sql("SELECT id, company_name FROM companies", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_company_ratios(ticker):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    df = pd.read_sql(
        "SELECT * FROM financial_ratios WHERE company_id = ? AND year != 'TTM' ORDER BY year",
        conn, params=(ticker,)
    )
    conn.close()
    return df


companies = get_companies_list()
companies["display"] = companies["id"] + " — " + companies["company_name"]

search = st.text_input("Search company", "")
matches = companies[companies["display"].str.contains(search, case=False, na=False)] if search else companies

if matches.empty:
    st.warning("Ticker not found — please try another")
else:
    selected = st.selectbox("Select company", matches["display"].tolist())
    ticker = selected.split(" — ")[0]

    metric_options = {
        "ROE": "return_on_equity_pct",
        "ROCE": "return_on_capital_employed_pct",
        "Net Profit Margin": "net_profit_margin_pct",
        "D/E": "debt_to_equity",
        "Revenue CAGR 5yr": "revenue_cagr_5yr",
        "Composite Score": "composite_quality_score",
    }
    selected_metrics = st.multiselect("Select up to 3 metrics", list(metric_options.keys()),
                                        default=["ROE"], max_selections=3)

    ratios = get_company_ratios(ticker)

    if ratios.empty:
        st.warning("No data available for this company.")
    elif not selected_metrics:
        st.info("Select at least one metric to view the trend.")
    else:
        ratios_10yr = ratios.tail(10)

        fig = go.Figure()
        for metric_label in selected_metrics:
            col = metric_options[metric_label]
            values = ratios_10yr[col]
            yoy_change = values.pct_change() * 100

            fig.add_trace(go.Scatter(
                x=ratios_10yr["year"], y=values, mode="lines+markers+text", name=metric_label,
                text=[f"{c:+.1f}%" if pd.notna(c) else "" for c in yoy_change],
                textposition="top center",
            ))

        st.plotly_chart(fig, use_container_width=True)