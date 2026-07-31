"""Manual verification for the screener engine — Sprint 3, Day 15."""

import sqlite3
import pandas as pd

from src.screener.engine import build_screener_dataset, load_config
from src.screener.engine import apply_filters

DB_PATH = "data/nifty100.db"



if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    dataset = build_screener_dataset(conn)

    from src.screener.engine import compute_revenue_cagr_3yr_for_screener

    ratios_all_years = pd.read_sql("SELECT * FROM financial_ratios", conn)
    ratios_all_years = ratios_all_years[ratios_all_years["year"].str.endswith("-03")]

    count_checked = 0
    count_cagr_ok = 0
    count_none = 0

    for company_id in dataset["company_id"].unique():
        company_history = ratios_all_years[ratios_all_years["company_id"] == company_id].sort_values("year")
        if len(company_history) < 2:
            continue
        latest = company_history.iloc[-1]
        count_checked += 1

        cagr = compute_revenue_cagr_3yr_for_screener(conn, company_id, latest["year"])
        if cagr is None:
            count_none += 1
        elif cagr > 10:
            count_cagr_ok += 1

    print("Companies checked:", count_checked)
    print("3yr CAGR is None (insufficient data):", count_none)
    print("3yr CAGR > 10%:", count_cagr_ok)

    conn.close()
    