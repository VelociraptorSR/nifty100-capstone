"""Manual/ad-hoc verification script for ratio calculations — Sprint 2.

Not a formal pytest file (see tests/kpi/ for that) — just a quick way
to eyeball real computed values against real data during development.
"""

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
    compute_debt_to_equity,
    compute_high_leverage_flag,
    compute_interest_coverage,
    compute_icr_label,
    compute_icr_risk_flag,
    compute_net_debt,
    compute_asset_turnover,
)

DB_PATH = "data/nifty100.db"


def preview_leverage(merged_df, company_id, broad_sector, n=3):
    sample = merged_df[merged_df["company_id"] == company_id].head(n)
    for _, row in sample.iterrows():
        de = compute_debt_to_equity(row)
        high_lev = compute_high_leverage_flag(de, broad_sector)
        icr = compute_interest_coverage(row)
        icr_label = compute_icr_label(icr, row["borrowings"])
        icr_risk = compute_icr_risk_flag(icr)
        net_debt = compute_net_debt(row)
        asset_turnover = compute_asset_turnover(row)

        print(f"{row['company_id']} {row['year']}:")
        print(f"  D/E = {de}, high_leverage_flag = {high_lev}")
        print(f"  ICR = {icr} ({icr_label}), risk_flag = {icr_risk}")
        print(f"  Net Debt = {net_debt}")
        print(f"  Asset Turnover = {asset_turnover}")
        print()
        
        
if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    merged = get_pl_bs_merged(conn)

    preview_leverage(merged, "ABB", "Healthcare")
    preview_leverage(merged, "CANBK", "Financials")

    conn.close()