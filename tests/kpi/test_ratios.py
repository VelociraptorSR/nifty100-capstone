"""Unit tests for src/analytics/ratios.py — profitability ratios. Sprint 2, Day 08."""

import pandas as pd
import pytest

from src.analytics.ratios import (
    compute_net_profit_margin,
    compute_operating_profit_margin,
    compute_roe,
    compute_roce,
    compute_roa,
)

from src.analytics.ratios import (
    compute_debt_to_equity,
    compute_high_leverage_flag,
    compute_interest_coverage,
    compute_icr_label,
    compute_icr_risk_flag,
    compute_net_debt,
    compute_asset_turnover,
)

def test_npm_normal_case():
    row = pd.Series({"sales": 1000, "net_profit": 100})
    assert compute_net_profit_margin(row) == 10.0


def test_npm_zero_sales_returns_none():
    row = pd.Series({"sales": 0, "net_profit": 100})
    assert compute_net_profit_margin(row) is None


def test_opm_normal_case_no_mismatch():
    row = pd.Series({"sales": 1000, "operating_profit": 200, "opm_percentage": 20.0})
    opm, mismatch = compute_operating_profit_margin(row)
    assert opm == 20.0
    assert mismatch == False


def test_opm_cross_check_mismatch_detected():
    row = pd.Series({"sales": 1000, "operating_profit": 200, "opm_percentage": 50.0})
    opm, mismatch = compute_operating_profit_margin(row)
    assert opm == 20.0
    assert mismatch == True


def test_roe_normal_case():
    row = pd.Series({"net_profit": 100, "equity_capital": 400, "reserves": 600})
    assert compute_roe(row) == 10.0


def test_roe_negative_equity_returns_none():
    row = pd.Series({"net_profit": 100, "equity_capital": 10, "reserves": -50})
    assert compute_roe(row) is None


def test_roce_normal_case():
    row = pd.Series({"operating_profit": 300, "depreciation": 50,
                      "equity_capital": 400, "reserves": 600, "borrowings": 500})
    assert compute_roce(row) == pytest.approx(16.6667, rel=1e-3)


def test_roa_zero_assets_returns_none():
    row = pd.Series({"net_profit": 100, "total_assets": 0})
    assert compute_roa(row) is None


def test_de_debt_free_returns_zero():
    row = pd.Series({"borrowings": 0, "equity_capital": 400, "reserves": 600})
    assert compute_debt_to_equity(row) == 0


def test_de_normal_case():
    row = pd.Series({"borrowings": 500, "equity_capital": 400, "reserves": 600})
    assert compute_debt_to_equity(row) == 0.5


def test_high_leverage_flag_triggers_for_non_financial():
    assert compute_high_leverage_flag(6.0, "Industrials") == True


def test_high_leverage_flag_suppressed_for_financials():
    assert compute_high_leverage_flag(15.0, "Financials") == False


def test_icr_interest_zero_returns_none():
    row = pd.Series({"interest": 0, "operating_profit": 500, "other_income": 50})
    assert compute_interest_coverage(row) is None


def test_icr_label_debt_free():
    label = compute_icr_label(None, borrowings=0)
    assert label == "Debt Free"


def test_icr_risk_flag_triggers_below_threshold():
    assert compute_icr_risk_flag(1.2) == True


def test_asset_turnover_zero_assets_returns_none():
    row = pd.Series({"sales": 1000, "total_assets": 0})
    assert compute_asset_turnover(row) is None