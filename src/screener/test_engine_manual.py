"""Manual verification for the screener engine — Sprint 3, Day 15."""

import sqlite3

from src.screener.engine import build_screener_dataset, load_config
from src.screener.engine import apply_filters

DB_PATH = "data/nifty100.db"



if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    dataset = build_screener_dataset(conn)
    conn.close()

    config = load_config()

    result = apply_filters(dataset, {"roe_min": 15, "de_max": 1.0}, config)
    print("Filtered result count:", len(result))
    print(result[["company_id", "return_on_equity_pct", "debt_to_equity", "composite_quality_score"]].head(10))