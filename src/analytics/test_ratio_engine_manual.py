"""Manual verification for the full ratio engine pipeline — Day 12."""
import pandas as pd
import sqlite3

from src.analytics.ratio_engine import build_full_dataset, build_ratio_row

DB_PATH = "data/nifty100.db"

if __name__ == "__main__":
    from src.analytics.ratio_engine import (
        compute_all_ratios, write_financial_ratios,
        get_latest_year_ratios, cross_check_roce, cross_check_roe,
        generate_edge_case_log,
    )

    conn = sqlite3.connect(DB_PATH)

    ratios_df = compute_all_ratios(conn)
    write_financial_ratios(conn, ratios_df)
    print("financial_ratios rows written:", len(ratios_df))

    companies_df = pd.read_sql("SELECT id, roce_percentage, roe_percentage FROM companies", conn)
    latest = get_latest_year_ratios(ratios_df)

    roce_anomalies = cross_check_roce(latest, companies_df)
    roe_anomalies = cross_check_roe(latest, companies_df)
    generate_edge_case_log(roce_anomalies, roe_anomalies)
    print("ROCE anomalies:", len(roce_anomalies), "| ROE anomalies:", len(roe_anomalies))

    conn.close()
    
