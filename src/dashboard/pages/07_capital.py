"""Capital Allocation Map Screen — Sprint 4, Day 25."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Capital Allocation Map")


@st.cache_data(ttl=600)
def get_capital_allocation():
    return pd.read_csv("output/capital_allocation.csv")


capital_data = get_capital_allocation()

capital_data["year_sortable"] = capital_data["year"].astype(str).str.replace("-", "").astype(int)
idx = capital_data.groupby("company_id")["year_sortable"].idxmax()
latest = capital_data.loc[idx]

pattern_counts = latest["pattern_label"].value_counts().reset_index()
pattern_counts.columns = ["pattern_label", "count"]

fig = px.treemap(pattern_counts, path=["pattern_label"], values="count")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Explore a Pattern")
selected_pattern = st.selectbox("Select a capital allocation pattern", sorted(latest["pattern_label"].unique()))

companies_in_pattern = latest[latest["pattern_label"] == selected_pattern]
st.write(f"**{len(companies_in_pattern)} companies** with pattern: {selected_pattern}")
st.dataframe(companies_in_pattern[["company_id", "year", "cfo_sign", "cfi_sign", "cff_sign"]], hide_index=True)