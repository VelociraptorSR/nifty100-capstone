"""Screener Screen — Sprint 4, Day 24."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import streamlit as st
import sqlite3

from src.screener.engine import build_screener_dataset, apply_filters, load_config

st.title("Screener")

DB_PATH = "data/nifty100.db"


@st.cache_data(ttl=600)
def get_dataset():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    dataset = build_screener_dataset(conn)
    conn.close()
    return dataset


@st.cache_data(ttl=600)
def get_config():
    return load_config()


dataset = get_dataset()
config = get_config()

PRESET_DEFAULTS = {
    "Quality": {"roe_min": 15, "de_max": 1.0, "fcf_min": 0, "revenue_cagr_5yr_min": 10},
    "Value": {"pe_max": 20, "pb_max": 3.0, "de_max": 2.0, "dividend_yield_min": 1},
    "Growth": {"pat_cagr_5yr_min": 20, "revenue_cagr_5yr_min": 15, "de_max": 2.0},
    "Dividend": {"dividend_yield_min": 2, "fcf_min": 0, "dividend_payout_max": 80},
    "Debt-Free": {"de_max": 0.05, "roe_min": 12, "sales_min": 5000},
}

if "screener_values" not in st.session_state:
    st.session_state.screener_values = {}

st.sidebar.subheader("Presets")
preset_cols = st.sidebar.columns(2)
preset_names = list(PRESET_DEFAULTS.keys())
for i, name in enumerate(preset_names):
    if preset_cols[i % 2].button(name):
        st.session_state.screener_values = PRESET_DEFAULTS[name].copy()

st.sidebar.subheader("Filters")

defaults = st.session_state.screener_values

roe_min = st.sidebar.slider("ROE min (%)", -50, 100, int(defaults.get("roe_min", -50)))
de_max = st.sidebar.slider("D/E max", 0.0, 20.0, float(defaults.get("de_max", 20.0)))
fcf_min = st.sidebar.slider("FCF min (Cr)", -5000, 50000, int(defaults.get("fcf_min", -5000)))
revenue_cagr_min = st.sidebar.slider("Revenue CAGR 5yr min (%)", -20, 50, int(defaults.get("revenue_cagr_5yr_min", -20)))
pat_cagr_min = st.sidebar.slider("PAT CAGR 5yr min (%)", -50, 100, int(defaults.get("pat_cagr_5yr_min", -50)))
opm_min = st.sidebar.slider("OPM min (%)", -20, 60, int(defaults.get("opm_min", -20)))
pe_max = st.sidebar.slider("P/E max", 0, 100, int(defaults.get("pe_max", 100)))
pb_max = st.sidebar.slider("P/B max", 0.0, 20.0, float(defaults.get("pb_max", 20.0)))
dividend_yield_min = st.sidebar.slider("Dividend Yield min (%)", 0.0, 5.0, float(defaults.get("dividend_yield_min", 0.0)))
icr_min = st.sidebar.slider("ICR min", 0.0, 20.0, float(defaults.get("icr_min", 0.0)))

active_filters = {
    "roe_min": roe_min,
    "de_max": de_max,
    "fcf_min": fcf_min,
    "revenue_cagr_5yr_min": revenue_cagr_min,
    "pat_cagr_5yr_min": pat_cagr_min,
    "opm_min": opm_min,
    "pe_max": pe_max,
    "pb_max": pb_max,
    "dividend_yield_min": dividend_yield_min,
    "icr_min": icr_min,
}

result = apply_filters(dataset, active_filters, config)

st.write(f"**{len(result)} companies match your filters**")

display_cols = ["company_id", "company_name", "broad_sector", "composite_quality_score",
                 "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr",
                 "revenue_cagr_5yr", "pe_ratio", "dividend_yield_pct"]
display_cols = [c for c in display_cols if c in result.columns]

st.dataframe(result[display_cols], hide_index=True, use_container_width=True)

csv = result[display_cols].to_csv(index=False)
st.download_button("Download CSV", csv, file_name="screener_results.csv", mime="text/csv")