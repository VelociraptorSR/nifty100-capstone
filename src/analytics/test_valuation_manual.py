"""Manual verification for the valuation module — Sprint 4, Day 26."""

import sqlite3

from src.analytics.valuation import compute_valuation_summary

DB_PATH = "data/nifty100.db"

if __name__ == "__main__":
    from src.analytics.valuation import compute_valuation_summary, export_valuation_summary, export_valuation_flags

    conn = sqlite3.connect(DB_PATH)
    summary = compute_valuation_summary(conn)
    conn.close()

    path1 = export_valuation_summary(summary)
    print("Saved:", path1)

    path2 = export_valuation_flags(summary)
    print("Saved:", path2)

    import pandas as pd
    flags_check = pd.read_csv(path2)
    print("Flagged companies:", len(flags_check))