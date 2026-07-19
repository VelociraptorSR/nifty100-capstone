"""Day 06 manual data quality review — Sprint 1.

Inspects 5 randomly sampled companies across all time-series tables
to visually verify correctness, per Section 12 Sprint 1 Day 06 spec.
"""

import sqlite3
import pandas as pd

DB_PATH = "data/nifty100.db"


def review_company(conn, company_id):
    """Print P&L, balance sheet, and cash flow history for one company."""
    print(f"===== {company_id} =====")

    pl = pd.read_sql(
        "SELECT year, sales, net_profit FROM profitandloss WHERE company_id = ? ORDER BY year",
        conn, params=(company_id,)
    )
    print(f"P&L years: {len(pl)}")
    print(pl)
    print()

    bs = pd.read_sql(
        "SELECT year, total_assets, total_liabilities FROM balancesheet WHERE company_id = ? ORDER BY year",
        conn, params=(company_id,)
    )
    print(f"Balance Sheet years: {len(bs)}")
    print(bs)
    print()

    cf = pd.read_sql(
        "SELECT year, operating_activity, net_cash_flow FROM cashflow WHERE company_id = ? ORDER BY year",
        conn, params=(company_id,)
    )
    print(f"Cash Flow years: {len(cf)}")
    print(cf)
    print()
    
def check_abb_cashflow(conn):
    """Quick verification that ABB's cash flow conflict was resolved correctly."""
    abb = pd.read_sql(
        "SELECT year, operating_activity, net_cash_flow FROM cashflow WHERE company_id = ? ORDER BY year",
        conn, params=("ABB",)
    )
    print("ABB cashflow rows:", len(abb))
    print(abb)


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)

    check_abb_cashflow(conn)

    conn.close()