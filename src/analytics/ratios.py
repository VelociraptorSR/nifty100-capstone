"""Financial Ratio Engine — profitability, leverage, and efficiency ratios.

Sprint 2, Day 08 onward. Computes KPIs from raw P&L/Balance Sheet/Cash
Flow data (not the pre-computed financial_ratios.xlsx, which is only
used for cross-validation per Section 9 Module 2 of the project spec).
"""

import sqlite3
import pandas as pd

DB_PATH = "data/nifty100.db"


def get_pl_bs_merged(conn):
    """Join profitandloss and balancesheet on (company_id, year).

    Returns one row per company-year with fields from both statements,
    needed for profitability ratio calculations.
    """
    pl = pd.read_sql("SELECT * FROM profitandloss", conn)
    bs = pd.read_sql("SELECT * FROM balancesheet", conn)

    merged = pd.merge(pl, bs, on=["company_id", "year"], suffixes=("_pl", "_bs"))
    return merged


def compute_net_profit_margin(row):
    """NPM = net_profit / sales x 100. None if sales = 0."""
    sales = row["sales"]
    net_profit = row["net_profit"]
    if pd.isna(sales) or sales == 0:
        return None
    return (net_profit / sales) * 100


def compute_operating_profit_margin(row):
    """OPM = operating_profit / sales x 100. None if sales = 0.

    Also cross-checks against the source opm_percentage field —
    returns (computed_opm, mismatch_flag) as a tuple.
    """
    sales = row["sales"]
    op_profit = row["operating_profit"]
    stated_opm = row.get("opm_percentage")

    if pd.isna(sales) or sales == 0:
        return None, False

    computed_opm = (op_profit / sales) * 100

    mismatch = False
    if pd.notna(stated_opm):
        mismatch = abs(computed_opm - stated_opm) > 1.0

    return computed_opm, mismatch


def compute_roe(row):
    """ROE = net_profit / (equity_capital + reserves) x 100. None if <= 0."""
    equity = row["equity_capital"] + row["reserves"]
    net_profit = row["net_profit"]
    if pd.isna(equity) or equity <= 0:
        return None
    return (net_profit / equity) * 100


def compute_roce(row):
    """ROCE = EBIT / (equity + reserves + borrowings) x 100.

    EBIT = operating_profit - depreciation. None if capital employed <= 0.
    """
    ebit = row["operating_profit"] - row["depreciation"]
    capital_employed = row["equity_capital"] + row["reserves"] + row["borrowings"]
    if pd.isna(capital_employed) or capital_employed <= 0:
        return None
    return (ebit / capital_employed) * 100


def compute_roa(row):
    """ROA = net_profit / total_assets x 100. None if total_assets = 0."""
    total_assets = row["total_assets"]
    net_profit = row["net_profit"]
    if pd.isna(total_assets) or total_assets == 0:
        return None
    return (net_profit / total_assets) * 100


def compute_debt_to_equity(row):
    """D/E = borrowings / (equity_capital + reserves).

    Returns 0 (not None) if borrowings = 0 — debt-free is a valid,
    meaningful result, not an undefined one.
    """
    borrowings = row["borrowings"]
    equity = row["equity_capital"] + row["reserves"]

    if pd.isna(borrowings) or borrowings == 0:
        return 0

    if pd.isna(equity) or equity <= 0:
        return None

    return borrowings / equity


def compute_high_leverage_flag(de_ratio, broad_sector):
    """True if D/E > 5 AND company is NOT in Financials sector.

    High D/E is structurally normal for banks/NBFCs (their business model
    is built on leverage), so the flag is suppressed for that sector.
    """
    if de_ratio is None:
        return False
    if broad_sector == "Financials":
        return False
    return de_ratio > 5


def compute_interest_coverage(row):
    """ICR = (operating_profit + other_income) / interest.

    Returns None if interest = 0 — but this is a GOOD outcome (debt-free),
    so a separate icr_label column stores 'Debt Free' for display.
    """
    interest = row["interest"]
    op_profit = row["operating_profit"]
    other_income = row["other_income"] if pd.notna(row["other_income"]) else 0

    if pd.isna(interest) or interest == 0:
        return None

    return (op_profit + other_income) / interest


def compute_icr_label(icr_value, borrowings):
    """Display label for ICR: 'Debt Free' when ICR is None due to zero
    interest, otherwise a formatted numeric string.
    """
    if icr_value is None:
        if borrowings == 0 or pd.isna(borrowings):
            return "Debt Free"
        return "N/A"
    return f"{icr_value:.2f}x"


def compute_icr_risk_flag(icr_value):
    """True if ICR < 1.5 — company may struggle to cover interest payments.

    None (debt-free) is never a risk, so it returns False, not True.
    """
    if icr_value is None:
        return False
    return icr_value < 1.5


def compute_net_debt(row):
    """Net Debt = borrowings - investments (investments as liquid asset proxy)."""
    borrowings = row["borrowings"] if pd.notna(row["borrowings"]) else 0
    investments = row["investments"] if pd.notna(row["investments"]) else 0
    return borrowings - investments


def compute_asset_turnover(row):
    """Asset Turnover = sales / total_assets. None if total_assets = 0."""
    total_assets = row["total_assets"]
    sales = row["sales"]
    if pd.isna(total_assets) or total_assets == 0:
        return None
    return sales / total_assets