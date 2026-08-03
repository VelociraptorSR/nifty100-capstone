"""Manual verification for the screener engine — Sprint 3, Day 15."""

import sqlite3
import pandas as pd

from src.screener.engine import build_screener_dataset, load_config
from src.screener.engine import apply_filters

DB_PATH = "data/nifty100.db"



if __name__ == "__main__":
    from src.screener.engine import build_screener_dataset, run_preset, load_config, compute_sector_relative_composite_score

    conn = sqlite3.connect(DB_PATH)
    dataset = build_screener_dataset(conn)
    config = load_config()

    result = run_preset(dataset, "quality_compounder", config)
    result = result.sort_values("composite_quality_score", ascending=False)

    print("Quality Compounder - Top 5:")
    print(result[["company_id", "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr", "revenue_cagr_5yr"]].head(5))

    conn.close()