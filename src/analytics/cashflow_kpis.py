"""Cash Flow KPIs and Capital Allocation classifier.

Sprint 2, Day 11. Computes Free Cash Flow, CFO Quality Score, CapEx
Intensity, FCF Conversion Rate, and the 8-pattern capital allocation
classifier per Section 10, Module 7 of the project spec.
"""

import sqlite3
import pandas as pd

DB_PATH = "data/nifty100.db"


def get_pl_cf_merged(conn):
    """Join profitandloss and cashflow on (company_id, year)."""
    pl = pd.read_sql("SELECT * FROM profitandloss", conn)
    cf = pd.read_sql("SELECT * FROM cashflow", conn)
    merged = pd.merge(pl, cf, on=["company_id", "year"], suffixes=("_pl", "_cf"))
    return merged


def compute_fcf(row):
    """Free Cash Flow = operating_activity + investing_activity.

    Negative FCF is a valid, meaningful result (company is investing
    or burning cash) — never returns None.
    """
    cfo = row["operating_activity"]
    cfi = row["investing_activity"]
    return cfo + cfi


def compute_capex_intensity(row):
    """CapEx Intensity = abs(investing_activity) / sales x 100.

    <3% = Asset Light, 3-8% = Moderate, >8% = Capital Intensive.
    Returns (value, label). None/'N/A' if sales = 0.
    """
    sales = row["sales"]
    cfi = row["investing_activity"]

    if pd.isna(sales) or sales == 0:
        return None, "N/A"

    intensity = abs(cfi) / sales * 100

    if intensity < 3:
        label = "Asset Light"
    elif intensity <= 8:
        label = "Moderate"
    else:
        label = "Capital Intensive"

    return intensity, label


def compute_fcf_conversion_rate(row):
    """FCF Conversion Rate = FCF / operating_profit x 100.

    None if operating_profit = 0.
    """
    fcf = compute_fcf(row)
    op_profit = row["operating_profit"]

    if pd.isna(op_profit) or op_profit == 0:
        return None

    return (fcf / op_profit) * 100

def compute_cfo_quality_score(company_df, current_year, window=5):
    """CFO Quality Score: average(CFO/PAT) over the trailing window years.

    >1.0 = High Quality, 0.5-1.0 = Moderate, <0.5 = Accrual Risk.
    Returns (score, label). None/'Insufficient Data' if PAT = 0 in any
    year of the window, or fewer than `window` years are available.
    """
    clean_df = company_df[company_df["year"] != "TTM"].copy()
    clean_df["year_num"] = clean_df["year"].str[:4].astype(int)

    current_year_num = int(current_year[:4])
    window_years = list(range(current_year_num - window + 1, current_year_num + 1))

    window_df = clean_df[clean_df["year_num"].isin(window_years)]

    if len(window_df) < window:
        return None, "Insufficient Data"

    if (window_df["net_profit"] == 0).any():
        return None, "Insufficient Data"

    ratios = window_df["operating_activity"] / window_df["net_profit"]
    avg_ratio = ratios.mean()

    if avg_ratio > 1.0:
        label = "High Quality"
    elif avg_ratio >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"

    return avg_ratio, label


def classify_capital_allocation(row, cfo_quality_score=None):
    """Classify a company-year into a capital allocation pattern based on
    the sign of (CFO, CFI, CFF), with CFO/PAT quality distinguishing
    Reinvestor from Shareholder Returns within the (+,-,-) pattern.

    Returns (cfo_sign, cfi_sign, cff_sign, pattern_label).
    """
    cfo = row["operating_activity"]
    cfi = row["investing_activity"]
    cff = row["financing_activity"]

    cfo_sign = "+" if cfo >= 0 else "-"
    cfi_sign = "+" if cfi >= 0 else "-"
    cff_sign = "+" if cff >= 0 else "-"

    pattern = (cfo_sign, cfi_sign, cff_sign)

    if pattern == ("+", "-", "-"):
        if cfo_quality_score is not None and cfo_quality_score > 1.0:
            return cfo_sign, cfi_sign, cff_sign, "Shareholder Returns"
        return cfo_sign, cfi_sign, cff_sign, "Reinvestor"

    pattern_labels = {
        ("+", "+", "-"): "Liquidating Assets",
        ("-", "+", "+"): "Distress Signal",
        ("-", "-", "+"): "Growth Funded by Debt",
        ("+", "+", "+"): "Cash Accumulator",
        ("-", "-", "-"): "Pre-Revenue",
        ("+", "-", "+"): "Mixed",
        ("-", "+", "-"): "Mixed",
    }

    return cfo_sign, cfi_sign, cff_sign, pattern_labels.get(pattern, "Mixed")


def generate_capital_allocation_csv(conn, output_path="output/capital_allocation.csv"):
    """Generate the capital_allocation.csv deliverable for all companies."""
    merged = get_pl_cf_merged(conn)
    merged = merged[merged["year"] != "TTM"].reset_index(drop=True)

    records = []
    for company_id in merged["company_id"].unique():
        company_series = merged[merged["company_id"] == company_id]
        for _, row in company_series.iterrows():
            quality_score, _ = compute_cfo_quality_score(company_series, row["year"])
            cfo_sign, cfi_sign, cff_sign, pattern_label = classify_capital_allocation(
                row, cfo_quality_score=quality_score
            )
            records.append({
                "company_id": row["company_id"],
                "year": row["year"],
                "cfo_sign": cfo_sign,
                "cfi_sign": cfi_sign,
                "cff_sign": cff_sign,
                "pattern_label": pattern_label,
            })

    result_df = pd.DataFrame(records)
    result_df.to_csv(output_path, index=False)
    return result_df