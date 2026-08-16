"""Manual verification for cash flow intelligence — Sprint 5, Day 31."""

import sqlite3

from src.analytics.cashflow_kpis import build_cashflow_intelligence

DB_PATH = "data/nifty100.db"

if __name__ == "__main__":
    import pandas as pd
    df = pd.read_csv("output/capital_allocation.csv")
    ambuja = df[df["company_id"] == "AMBUJACEM"].sort_values("year")
    print(ambuja[["year", "pattern_label"]])