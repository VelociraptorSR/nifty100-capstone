"""Manual verification for cash flow intelligence — Sprint 5, Day 31."""

import sqlite3

from src.analytics.cashflow_kpis import build_cashflow_intelligence

DB_PATH = "data/nifty100.db"

if __name__ == "__main__":
    from src.analytics.cashflow_kpis import build_cashflow_intelligence, export_cashflow_intelligence, export_distress_alerts

    conn = sqlite3.connect(DB_PATH)
    result = build_cashflow_intelligence(conn)
    conn.close()

    print("Total rows:", len(result))

    path1 = export_cashflow_intelligence(result)
    print("Saved:", path1)

    path2, distress_count = export_distress_alerts(result)
    print("Saved:", path2, "-", distress_count, "companies flagged")

    import pandas as pd
    check = pd.read_csv(path2)
    print(check[["company_id", "broad_sector", "note"]])