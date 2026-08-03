"""Nifty 100 Analytics — Streamlit Dashboard Entry Point.

Sprint 4, Day 22. Main app file; actual screens live in pages/.
"""

import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Nifty 100 Financial Intelligence Platform")
st.write(
    "Use the sidebar to navigate between screens: Home, Company Profile, "
    "Screener, Peer Comparison, Trend Analysis, Sector Analysis, "
    "Capital Allocation Map, and Annual Reports."
)