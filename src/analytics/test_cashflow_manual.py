"""Manual verification script for cash flow KPIs — Sprint 2, Day 11."""

import sqlite3

from src.analytics.cashflow_kpis import (
    get_pl_cf_merged,
    compute_fcf,
    compute_capex_intensity,
    compute_fcf_conversion_rate,
)

from src.analytics.cashflow_kpis import compute_cfo_quality_score
import pandas as pd
from src.analytics.cashflow_kpis import classify_capital_allocation

DB_PATH = "data/nifty100.db"


def preview_cashflow_kpis(merged_df, company_id, n=3):
    sample = merged_df[merged_df["company_id"] == company_id].head(n)
    for _, row in sample.iterrows():
        fcf = compute_fcf(row)
        capex_intensity, capex_label = compute_capex_intensity(row)
        fcf_conversion = compute_fcf_conversion_rate(row)

        print(f"{row['company_id']} {row['year']}:")
        print(f"  FCF = {fcf}")
        print(f"  CapEx Intensity = {capex_intensity} ({capex_label})")
        print(f"  FCF Conversion Rate = {fcf_conversion}")
        print()


if __name__ == "__main__":
    from src.analytics.cashflow_kpis import generate_capital_allocation_csv

    conn = sqlite3.connect(DB_PATH)

    df = generate_capital_allocation_csv(conn)
    print("Total rows:", len(df))
    print(df["pattern_label"].value_counts())

    conn.close()