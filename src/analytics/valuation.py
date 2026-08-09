"""Valuation Module — Sprint 4, Day 26.

Computes FCF yield and sector-relative overvaluation/discount flags
using market_cap.xlsx data, per Section 26 of the project spec.
"""

import sqlite3
import pandas as pd

DB_PATH = "data/nifty100.db"


def get_latest_year_per_company(df, year_col="year"):
    """Reduce a multi-year DataFrame to just each company's latest year."""
    df = df.copy()
    if df[year_col].dtype == object:
        df["_year_sortable"] = df[year_col].str.replace("-", "").astype(int)
    else:
        df["_year_sortable"] = df[year_col]
    idx = df.groupby("company_id")["_year_sortable"].idxmax()
    return df.loc[idx].drop(columns=["_year_sortable"])


def build_valuation_dataset(conn):
    """Combine market_cap + financial_ratios (FCF) + sectors + companies,
    reduced to each company's latest available year.
    """
    market_cap = pd.read_sql("SELECT * FROM market_cap", conn)
    market_cap = get_latest_year_per_company(market_cap)

    ratios = pd.read_sql("SELECT company_id, year, free_cash_flow_cr FROM financial_ratios", conn)
    ratios = get_latest_year_per_company(ratios)

    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT id, company_name FROM companies", conn)

    merged = market_cap.merge(ratios.drop(columns=["year"]), on="company_id", how="left")
    merged = merged.merge(sectors, on="company_id", how="left")
    merged = merged.merge(companies, left_on="company_id", right_on="id", how="left")

    return merged


def compute_fcf_yield(row):
    """FCF Yield = FCF / market_cap_crore x 100. None if market_cap = 0/missing."""
    market_cap = row["market_cap_crore"]
    fcf = row["free_cash_flow_cr"]
    if pd.isna(market_cap) or market_cap == 0 or pd.isna(fcf):
        return None
    return (fcf / market_cap) * 100


def compute_sector_median_pe(dataset):
    """Sector median P/E for each broad_sector, latest year."""
    return dataset.groupby("broad_sector")["pe_ratio"].median()


def apply_valuation_flag(pe_ratio, sector_median_pe):
    """Caution if P/E > sector_median x 1.5, Discount if < x 0.7, else Fair."""
    if pd.isna(pe_ratio) or pd.isna(sector_median_pe) or sector_median_pe == 0:
        return "Unknown"
    if pe_ratio > sector_median_pe * 1.5:
        return "Caution"
    if pe_ratio < sector_median_pe * 0.7:
        return "Discount"
    return "Fair"


def compute_5yr_median_pe(conn):
    """5-year median P/E per company, using all available years in market_cap
    (up to 6 years available: 2019-2024)."""
    mc = pd.read_sql("SELECT company_id, year, pe_ratio FROM market_cap", conn)
    mc_sorted = mc.sort_values(["company_id", "year"])
    recent_5yr = mc_sorted.groupby("company_id").tail(5)
    return recent_5yr.groupby("company_id")["pe_ratio"].median()


def compute_valuation_summary(conn):
    """Full valuation pipeline: FCF yield, sector median P/E, 5yr median P/E, flags."""
    dataset = build_valuation_dataset(conn)

    dataset["fcf_yield_pct"] = dataset.apply(compute_fcf_yield, axis=1)

    sector_medians = compute_sector_median_pe(dataset)
    dataset["sector_median_pe"] = dataset["broad_sector"].map(sector_medians)

    five_yr_median = compute_5yr_median_pe(conn)
    dataset["5yr_median_pe"] = dataset["company_id"].map(five_yr_median)

    dataset["pe_vs_sector_median_pct"] = (
        (dataset["pe_ratio"] - dataset["sector_median_pe"]) / dataset["sector_median_pe"] * 100
    )

    dataset["flag"] = dataset.apply(
        lambda row: apply_valuation_flag(row["pe_ratio"], row["sector_median_pe"]), axis=1
    )

    return dataset

def export_valuation_summary(summary_df, output_path="output/valuation_summary.xlsx"):
    """Generate valuation_summary.xlsx with the required columns."""
    export_cols = [
        "company_id", "company_name", "broad_sector", "pe_ratio", "pb_ratio",
        "ev_ebitda", "fcf_yield_pct", "5yr_median_pe", "pe_vs_sector_median_pct", "flag",
    ]
    export_cols = [c for c in export_cols if c in summary_df.columns]
    summary_df[export_cols].to_excel(output_path, index=False)
    return output_path


def export_valuation_flags(summary_df, output_path="output/valuation_flags.csv"):
    """Generate valuation_flags.csv — only Caution/Discount flagged companies."""
    flagged = summary_df[summary_df["flag"].isin(["Caution", "Discount"])]
    export_cols = [
        "company_id", "company_name", "broad_sector", "pe_ratio",
        "sector_median_pe", "pe_vs_sector_median_pct", "flag",
    ]
    export_cols = [c for c in export_cols if c in flagged.columns]
    flagged[export_cols].to_csv(output_path, index=False)
    return output_path