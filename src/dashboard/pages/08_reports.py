"""Annual Reports Screen — Sprint 4, Day 25."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import streamlit as st
import pandas as pd
import sqlite3

st.title("Annual Reports")

DB_PATH = "data/nifty100.db"


@st.cache_data(ttl=600)
def get_companies_list():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    df = pd.read_sql("SELECT id, company_name FROM companies", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_documents(ticker):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    df = pd.read_sql(
        "SELECT year, annual_report FROM documents WHERE company_id = ? ORDER BY year DESC",
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

    docs = get_documents(ticker)

    if docs.empty:
        st.info("No annual reports available for this company.")
    else:
        for _, row in docs.iterrows():
            if pd.isna(row["annual_report"]) or not str(row["annual_report"]).startswith("http"):
                st.markdown(f"**{row['year']}** — :red-background[Report unavailable]")
            else:
                st.markdown(f"**{row['year']}** — [View Report]({row['annual_report']})")