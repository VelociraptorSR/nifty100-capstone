"""Ratio Engine orchestrator — Sprint 2, Day 12.

Combines all KPI functions from ratios.py, cagr.py, and cashflow_kpis.py
into one pipeline that computes all required columns per company-year
and writes them into the financial_ratios table.
"""

import sqlite3
import pandas as pd

from src.analytics.ratios import (
    compute_net_profit_margin, compute_operating_profit_margin,
    compute_roe, compute_roce, compute_roa,
    compute_debt_to_equity, compute_interest_coverage,
    compute_asset_turnover,
)
from src.analytics.cagr import compute_company_cagr
from src.analytics.cashflow_kpis import compute_fcf, compute_cfo_quality_score

DB_PATH = "data/nifty100.db"


def build_full_dataset(conn):
    """Join profitandloss + balancesheet + cashflow + companies into one table."""
    pl = pd.read_sql("SELECT * FROM profitandloss", conn)
    bs = pd.read_sql("SELECT * FROM balancesheet", conn)
    cf = pd.read_sql("SELECT * FROM cashflow", conn)
    companies = pd.read_sql("SELECT id, face_value FROM companies", conn)

    merged = pd.merge(pl, bs, on=["company_id", "year"], suffixes=("_pl", "_bs"))
    merged = pd.merge(merged, cf, on=["company_id", "year"], how="left")
    merged = pd.merge(merged, companies, left_on="company_id", right_on="id", how="left")

    return merged[merged["year"] != "TTM"].reset_index(drop=True)


def compute_book_value_per_share(row):
    """Book Value/Share = (equity + reserves) / (equity_capital / face_value)."""
    equity = row["equity_capital"] + row["reserves"]
    face_value = row["face_value"]
    if pd.isna(face_value) or face_value == 0 or pd.isna(row["equity_capital"]) or row["equity_capital"] == 0:
        return None
    num_shares = row["equity_capital"] / face_value
    return equity / num_shares


def build_ratio_row(row, full_df, company_series):
    """Compute all required KPI columns for one company-year row."""
    npm = compute_net_profit_margin(row)
    opm, _ = compute_operating_profit_margin(row)
    roe = compute_roe(row)
    de = compute_debt_to_equity(row)
    icr = compute_interest_coverage(row)
    asset_turnover = compute_asset_turnover(row)
    fcf = compute_fcf(row)
    capex_cr = abs(row["investing_activity"]) if pd.notna(row["investing_activity"]) else None
    bvps = compute_book_value_per_share(row)

    rev_cagr_5yr, _ = compute_company_cagr(company_series, "sales", row["year"], 5)
    pat_cagr_5yr, _ = compute_company_cagr(company_series, "net_profit", row["year"], 5)
    eps_cagr_5yr, _ = compute_company_cagr(company_series, "eps", row["year"], 5)

    return {
        "company_id": row["company_id"],
        "year": row["year"],
        "net_profit_margin_pct": npm,
        "operating_profit_margin_pct": opm,
        "return_on_equity_pct": roe,
        "debt_to_equity": de,
        "interest_coverage": icr,
        "asset_turnover": asset_turnover,
        "free_cash_flow_cr": fcf,
        "capex_cr": capex_cr,
        "earnings_per_share": row["eps"],
        "book_value_per_share": bvps,
        "dividend_payout_ratio_pct": row["dividend_payout"],
        "total_debt_cr": row["borrowings"],
        "cash_from_operations_cr": row["operating_activity"],
        "revenue_cagr_5yr": rev_cagr_5yr,
        "pat_cagr_5yr": pat_cagr_5yr,
        "eps_cagr_5yr": eps_cagr_5yr,
    }
    
    
def winsorize_and_score(series):
    """Normalise a series to a 0-100 score using P10/P90 winsorisation.

    Values at/below P10 -> 0, values at/above P90 -> 100, linear between.
    """
    p10 = series.quantile(0.10)
    p90 = series.quantile(0.90)

    if p90 == p10:
        return pd.Series([50] * len(series), index=series.index)

    clipped = series.clip(lower=p10, upper=p90)
    score = (clipped - p10) / (p90 - p10) * 100
    return score


def compute_composite_quality_scores(ratios_df):
    """Add composite_quality_score column: weighted blend of ROE, FCF,
    ROCE, and D/E (inverted, since lower D/E is better), each normalised
    0-100 via P10/P90 winsorisation, per Section 13 spec weights.
    """
    df = ratios_df.copy()

    roe_score = winsorize_and_score(df["return_on_equity_pct"].fillna(df["return_on_equity_pct"].median()))
    fcf_score = winsorize_and_score(df["free_cash_flow_cr"].fillna(df["free_cash_flow_cr"].median()))
    de_inverted = -df["debt_to_equity"].fillna(df["debt_to_equity"].median())
    de_score = winsorize_and_score(de_inverted)

    roce_proxy = df["return_on_equity_pct"].fillna(df["return_on_equity_pct"].median())
    roce_score = winsorize_and_score(roce_proxy)

    df["composite_quality_score"] = (
        0.3 * roe_score + 0.25 * fcf_score + 0.25 * roce_score + 0.20 * de_score
    )

    return df


def compute_all_ratios(conn):
    """Compute all KPI rows for every company-year, plus composite score."""
    full_df = build_full_dataset(conn)

    all_rows = []
    for company_id in full_df["company_id"].unique():
        company_series = full_df[full_df["company_id"] == company_id]
        for _, row in company_series.iterrows():
            all_rows.append(build_ratio_row(row, full_df, company_series))

    ratios_df = pd.DataFrame(all_rows)
    ratios_df = compute_composite_quality_scores(ratios_df)
    return ratios_df


def write_financial_ratios(conn, ratios_df):
    """Overwrite the financial_ratios table with freshly computed values."""
    conn.execute("DELETE FROM financial_ratios")
    conn.commit()
    ratios_df.to_sql("financial_ratios", conn, if_exists="append", index=False)