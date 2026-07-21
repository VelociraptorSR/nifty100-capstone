"""CAGR Engine — Compound Annual Growth Rate calculations.

Sprint 2, Day 10. Computes Revenue, PAT, and EPS CAGR for 3/5/10-year
windows, handling all 6 documented edge cases per Section 23.1 of the
project spec.
"""

import pandas as pd


def compute_cagr(start_value, end_value, n_years):
    """Core CAGR formula with all 6 edge case handlers.

    Returns (cagr_value, flag) where flag is None for a normal,
    successfully computed result, or one of:
    DECLINE_TO_LOSS, TURNAROUND, BOTH_NEGATIVE, ZERO_BASE, INSUFFICIENT
    """
    if start_value is None or end_value is None:
        return None, "INSUFFICIENT"

    if start_value == 0:
        return None, "ZERO_BASE"

    if start_value > 0 and end_value < 0:
        return None, "DECLINE_TO_LOSS"

    if start_value < 0 and end_value > 0:
        return None, "TURNAROUND"

    if start_value < 0 and end_value < 0:
        return None, "BOTH_NEGATIVE"

    cagr = ((end_value / start_value) ** (1 / n_years) - 1) * 100
    return cagr, None


def get_value_n_years_ago(company_series, current_year, n_years, value_column):
    """Find a company's value from exactly n_years before current_year.

    company_series must be a DataFrame with 'year' (YYYY-MM format,
    TTM excluded) and value_column, already filtered to one company.
    Returns None if that exact year isn't available (per INSUFFICIENT rule).
    """
    current_year_num = int(current_year[:4])
    target_year_num = current_year_num - n_years

    match = company_series[company_series["year"].str[:4].astype(int) == target_year_num]

    if match.empty:
        return None

    return match.iloc[0][value_column]


def compute_company_cagr(company_df, value_column, current_year, n_years):
    """Compute CAGR for one company, one metric, one window (3/5/10yr).

    company_df: full time-series for ONE company (all years, TTM excluded)
    value_column: e.g. 'sales', 'net_profit', 'eps'
    current_year: the 'end' year, e.g. '2024-03'
    n_years: 3, 5, or 10
    """
    clean_df = company_df[company_df["year"] != "TTM"]

    end_match = clean_df[clean_df["year"] == current_year]
    if end_match.empty:
        return None, "INSUFFICIENT"
    end_value = end_match.iloc[0][value_column]

    start_value = get_value_n_years_ago(clean_df, current_year, n_years, value_column)
    if start_value is None:
        return None, "INSUFFICIENT"

    return compute_cagr(start_value, end_value, n_years)