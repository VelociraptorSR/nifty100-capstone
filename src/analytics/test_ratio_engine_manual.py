"""Manual verification for the full ratio engine pipeline — Day 12."""

import sqlite3

from src.analytics.ratio_engine import build_full_dataset, build_ratio_row

DB_PATH = "data/nifty100.db"

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.execute("""
        SELECT year, COUNT(*) as total, SUM(CASE WHEN revenue_cagr_5yr IS NULL THEN 1 ELSE 0 END) as null_count
        FROM financial_ratios
        GROUP BY year
        ORDER BY year
    """)
    for row in cursor.fetchall():
        print(row)

    conn.close()