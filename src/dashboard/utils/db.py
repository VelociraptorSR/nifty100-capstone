"""Shared, cached database access functions for the Streamlit dashboard.

Sprint 4, Day 22. Every function here is cached with @st.cache_data
so repeated UI interactions don't re-query the database unnecessarily.
"""

import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = "data/nifty100.db"


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data(ttl=600)
def get_companies():
    """All 92 companies with sector info."""
    conn = get_connection()
    df = pd.read_sql("""
        SELECT c.id, c.company_name, c.about_company, c.website,
               s.broad_sector, s.sub_sector
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
    """, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    """financial_ratios rows for one company, optionally filtered to one year."""
    conn = get_connection()
    if year:
        df = pd.read_sql(
            "SELECT * FROM financial_ratios WHERE company_id = ? AND year = ?",
            conn, params=(ticker, year)
        )
    else:
        df = pd.read_sql(
            "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year",
            conn, params=(ticker,)
        )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pl(ticker):
    """profitandloss history for one company."""
    conn = get_connection()
    df = pd.read_sql(
        "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year",
        conn, params=(ticker,)
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_bs(ticker):
    """balancesheet history for one company."""
    conn = get_connection()
    df = pd.read_sql(
        "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year",
        conn, params=(ticker,)
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_cf(ticker):
    """cashflow history for one company."""
    conn = get_connection()
    df = pd.read_sql(
        "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year",
        conn, params=(ticker,)
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_sectors():
    """All sector mappings."""
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM sectors", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peers(group_name):
    """All companies in a given peer group."""
    conn = get_connection()
    df = pd.read_sql(
        "SELECT * FROM peer_groups WHERE peer_group_name = ?",
        conn, params=(group_name,)
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_valuation(ticker):
    """market_cap history for one company."""
    conn = get_connection()
    df = pd.read_sql(
        "SELECT * FROM market_cap WHERE company_id = ? ORDER BY year",
        conn, params=(ticker,)
    )
    conn.close()
    return df