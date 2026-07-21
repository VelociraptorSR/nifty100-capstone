"""Manual/ad-hoc verification script for ratio calculations — Sprint 2.

Not a formal pytest file (see tests/kpi/ for that) — just a quick way
to eyeball real computed values against real data during development.
"""

import sqlite3

from src.analytics.ratios import (
    get_pl_bs_merged,
    compute_net_profit_margin,
    compute_operating_profit_margin,
    compute_roe,
    compute_roce,
    compute_roa,
)

DB_PATH = "data/nifty100.db"


def preview_company(merged_df, company_id, n=3):
    sample = merged_df[merged_df["company_id"] == company_id].head(n)
    for _, row in sample.iterrows():
        npm = compute_net_profit_margin(row)
        opm, opm_mismatch = compute_operating_profit_margin(row)
        roe = compute_roe(row)
        roce = compute_roce(row)
        roa = compute_roa(row)

        print(f"{row['company_id']} {row['year']}:")
        print(f"  NPM  = {npm}")
        print(f"  OPM  = {opm} (mismatch={opm_mismatch})")
        print(f"  ROE  = {roe}")
        print(f"  ROCE = {roce}")
        print(f"  ROA  = {roa}")
        print()


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    merged = get_pl_bs_merged(conn)
    preview_company(merged, "ABB")
    preview_company(merged, "CANBK", n=5)
    conn.close()