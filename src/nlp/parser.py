"""NLP Analysis Text Parser — Sprint 5, Day 29.

Parses free-text growth fields in analysis.xlsx using regex, per
Section 9 Module 9 of the project spec.
"""

import re
import sqlite3
import pandas as pd

DB_PATH = "data/nifty100.db"

PATTERN = r"(\d+)\s*Years?:?\s*(-?[\d.]+)%"

TARGET_FIELDS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]


def parse_growth_text(text):
    """Extract (period_years, value_pct) from text like '10 Years: 21%'.

    Returns (period_years, value_pct) as (int, float), or (None, None)
    if the text doesn't match the expected pattern.
    """
    if pd.isna(text):
        return None, None

    match = re.search(PATTERN, str(text))
    if not match:
        return None, None

    period_years = int(match.group(1))
    value_pct = float(match.group(2))
    return period_years, value_pct

def parse_all_analysis_text(conn):
    """Parse all 4 target fields across every row in the analysis table.

    Returns (parsed_df, failures_df) — successfully parsed rows go into
    parsed_df; rows where the regex didn't match go into failures_df.
    """
    analysis = pd.read_sql("SELECT * FROM analysis", conn)

    parsed_records = []
    failure_records = []

    for _, row in analysis.iterrows():
        for field in TARGET_FIELDS:
            raw_text = row[field]
            period, value = parse_growth_text(raw_text)

            if period is None:
                if pd.notna(raw_text):
                    failure_records.append({
                        "company_id": row["company_id"],
                        "field": field,
                        "raw_text": raw_text,
                    })
                continue

            parsed_records.append({
                "company_id": row["company_id"],
                "metric_type": field,
                "period_years": period,
                "value_pct": value,
            })

    parsed_df = pd.DataFrame(parsed_records, columns=["company_id", "metric_type", "period_years", "value_pct"])
    failures_df = pd.DataFrame(failure_records, columns=["company_id", "field", "raw_text"])

    return parsed_df, failures_df

def save_parsed_results(parsed_df, failures_df, parsed_path="output/analysis_parsed.csv", failures_path="output/parse_failures.csv"):
    parsed_df.to_csv(parsed_path, index=False)
    failures_df.to_csv(failures_path, index=False)
    return parsed_path, failures_path

def cross_validate_cagr(conn, parsed_df, threshold=5.0):
    """Compare parsed compounded_sales_growth (5yr) against our own
    computed revenue_cagr_5yr from financial_ratios. Flags divergence
    beyond the threshold (percentage points) for manual review.
    """
    parsed_5yr_sales = parsed_df[
        (parsed_df["metric_type"] == "compounded_sales_growth") &
        (parsed_df["period_years"] == 5)
    ]

    ratios = pd.read_sql(
        "SELECT company_id, year, revenue_cagr_5yr FROM financial_ratios WHERE year != 'TTM'",
        conn
    )
    ratios_sorted = ratios.sort_values("year")
    latest_ratios = ratios_sorted.groupby("company_id").tail(1)

    merged = parsed_5yr_sales.merge(latest_ratios, on="company_id", how="left")

    merged["divergence"] = (merged["value_pct"] - merged["revenue_cagr_5yr"]).abs()
    flagged = merged[merged["divergence"] > threshold]

    return merged, flagged