"""Manual verification script for CAGR calculations — Sprint 2, Day 10."""

import sqlite3
import pandas as pd

from src.analytics.cagr import compute_company_cagr

DB_PATH = "data/nifty100.db"

from src.analytics.cagr import compute_cagr

def test_all_edge_cases():
    print("--- Edge case verification ---")
    print("Normal (100 -> 200, 5yr):", compute_cagr(100, 200, 5))
    print("Decline to loss (100 -> -50, 5yr):", compute_cagr(100, -50, 5))
    print("Turnaround (-100 -> 200, 5yr):", compute_cagr(-100, 200, 5))
    print("Both negative (-100 -> -50, 5yr):", compute_cagr(-100, -50, 5))
    print("Zero base (0 -> 200, 5yr):", compute_cagr(0, 200, 5))
    print("Insufficient (None -> 200, 5yr):", compute_cagr(None, 200, 5))
    
    
if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    pl = pd.read_sql("SELECT company_id, year, sales, net_profit FROM profitandloss", conn)
    conn.close()

    abb = pl[pl["company_id"] == "ABB"]
    print("ABB years available:", sorted(abb["year"].tolist()))
    print()

    for n in [3, 5, 10]:
        cagr, flag = compute_company_cagr(abb, "sales", "2024-03", n)
        print(f"Revenue CAGR ({n}yr): {cagr}, flag={flag}")

    print()
    test_all_edge_cases()