"""Peer Comparison Screen — Sprint 4, Day 24."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3

st.title("Peer Comparison")

DB_PATH = "data/nifty100.db"


@st.cache_data(ttl=600)
def get_peer_group_names():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    df = pd.read_sql("SELECT DISTINCT peer_group_name FROM peer_groups ORDER BY peer_group_name", conn)
    conn.close()
    return df["peer_group_name"].tolist()


@st.cache_data(ttl=600)
def get_group_data(group_name):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    members = pd.read_sql(
        "SELECT company_id, is_benchmark FROM peer_groups WHERE peer_group_name = ?",
        conn, params=(group_name,)
    )
    ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
    companies = pd.read_sql("SELECT id, company_name FROM companies", conn)
    conn.close()

    ratios["year_sortable"] = ratios["year"].str.replace("-", "").astype(int)
    idx = ratios.groupby("company_id")["year_sortable"].idxmax()
    ratios = ratios.loc[idx]

    merged = members.merge(ratios, on="company_id", how="left")
    merged = merged.merge(companies, left_on="company_id", right_on="id", how="left")
    return merged


group_names = get_peer_group_names()
selected_group = st.selectbox("Select Peer Group", group_names)

group_data = get_group_data(selected_group)

if group_data.empty:
    st.warning("No data available for this peer group.")
else:
    company_choice = st.selectbox("Select company to highlight", group_data["company_id"].tolist())

    axes = ["return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
            "debt_to_equity", "free_cash_flow_cr", "pat_cagr_5yr", "revenue_cagr_5yr", "composite_quality_score"]
    axis_labels = ["ROE", "ROCE", "NPM", "D/E", "FCF", "PAT CAGR", "Rev CAGR", "Composite"]

    from src.analytics.ratio_engine import winsorize_and_score
    normalized = group_data.copy()
    for m in axes:
        if m == "composite_quality_score":
            normalized[m] = normalized[m].fillna(normalized[m].median())
        else:
            vals = normalized[m].fillna(normalized[m].median())
            if m == "debt_to_equity":
                vals = -vals
            normalized[m] = winsorize_and_score(vals)

    company_row = normalized[normalized["company_id"] == company_choice].iloc[0]
    company_values = [company_row[a] for a in axes]
    peer_avg_values = [normalized[a].mean() for a in axes]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=company_values + company_values[:1], theta=axis_labels + axis_labels[:1],
                                    fill="toself", name=company_choice))
    fig.add_trace(go.Scatterpolar(r=peer_avg_values + peer_avg_values[:1], theta=axis_labels + axis_labels[:1],
                                    name=f"{selected_group} Avg", line=dict(dash="dash")))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))

    st.plotly_chart(fig, use_container_width=True)

    st.subheader(f"{selected_group} — Side by Side")
    display_cols = ["company_id", "company_name", "return_on_equity_pct", "debt_to_equity",
                     "free_cash_flow_cr", "composite_quality_score", "is_benchmark"]
    display_cols = [c for c in display_cols if c in group_data.columns]

    def highlight_benchmark(row):
        if row.get("is_benchmark"):
            return ["background-color: #FFD966"] * len(row)
        return [""] * len(row)

    st.dataframe(
        group_data[display_cols].style.apply(highlight_benchmark, axis=1),
        hide_index=True,
        use_container_width=True,
    )