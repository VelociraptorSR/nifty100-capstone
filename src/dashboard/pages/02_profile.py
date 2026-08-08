"""Company Profile Screen — Sprint 4, Day 23."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.dashboard.utils.db import get_companies, get_ratios, get_pl
import sqlite3

st.title("Company Profile")

DB_PATH = "data/nifty100.db"

companies = get_companies()
companies["display"] = companies["id"] + " — " + companies["company_name"]

search = st.text_input("Search by company name or ticker", "")

if search:
    matches = companies[
        companies["display"].str.contains(search, case=False, na=False)
    ]
else:
    matches = companies

if matches.empty:
    st.warning("Ticker not found — please try another")
else:
    selected_display = st.selectbox("Select company", matches["display"].tolist())
    ticker = selected_display.split(" — ")[0]

    company = companies[companies["id"] == ticker].iloc[0]

    st.subheader(f"{company['company_name']} ({ticker})")
    st.write(f"**Sector:** {company['broad_sector']} — {company['sub_sector']}")
    st.write(f"**About:** {company['about_company'] if pd.notna(company['about_company']) else 'No description available'}")

    ratios = get_ratios(ticker)

    if ratios.empty:
        st.warning("No financial data available for this company.")
    else:
        latest = ratios[ratios["year"] != "TTM"].sort_values("year").iloc[-1]

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("ROE", f"{latest['return_on_equity_pct']:.1f}%" if pd.notna(latest['return_on_equity_pct']) else "N/A")
        col2.metric("ROCE", f"{latest['return_on_capital_employed_pct']:.1f}%" if pd.notna(latest['return_on_capital_employed_pct']) else "N/A")
        col3.metric("NPM", f"{latest['net_profit_margin_pct']:.1f}%" if pd.notna(latest['net_profit_margin_pct']) else "N/A")
        col4.metric("D/E", f"{latest['debt_to_equity']:.2f}" if pd.notna(latest['debt_to_equity']) else "N/A")
        col5.metric("Revenue CAGR 5yr", f"{latest['revenue_cagr_5yr']:.1f}%" if pd.notna(latest['revenue_cagr_5yr']) else "N/A")
        col6.metric("FCF (Cr)", f"{latest['free_cash_flow_cr']:.0f}" if pd.notna(latest['free_cash_flow_cr']) else "N/A")

        st.divider()

        pl = get_pl(ticker)
        pl_clean = pl[pl["year"] != "TTM"].sort_values("year").tail(10)

        if not pl_clean.empty:
            st.subheader("Revenue & Net Profit (10-year)")
            fig = go.Figure()
            fig.add_trace(go.Bar(x=pl_clean["year"], y=pl_clean["sales"], name="Revenue"))
            fig.add_trace(go.Bar(x=pl_clean["year"], y=pl_clean["net_profit"], name="Net Profit"))
            fig.update_layout(barmode="group")
            st.plotly_chart(fig, use_container_width=True)

        ratios_clean = ratios[ratios["year"] != "TTM"].sort_values("year").tail(10)
        if not ratios_clean.empty:
            st.subheader("ROE & ROCE Trend (10-year)")
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=ratios_clean["year"], y=ratios_clean["return_on_equity_pct"], name="ROE", yaxis="y1"))
            fig2.add_trace(go.Scatter(x=ratios_clean["year"], y=ratios_clean["return_on_capital_employed_pct"], name="ROCE", yaxis="y2"))
            fig2.update_layout(
                yaxis=dict(title="ROE %"),
                yaxis2=dict(title="ROCE %", overlaying="y", side="right"),
            )
            st.plotly_chart(fig2, use_container_width=True)

        st.divider()
        st.subheader("Pros & Cons")

        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        proscons = pd.read_sql("SELECT pros, cons FROM prosandcons WHERE company_id = ?", conn, params=(ticker,))
        conn.close()

        if proscons.empty:
            st.write("No pros/cons data available for this company.")
        else:
            for _, row in proscons.iterrows():
                if pd.notna(row["pros"]):
                    st.success(f"✅ {row['pros']}")
                if pd.notna(row["cons"]):
                    st.error(f"❌ {row['cons']}")