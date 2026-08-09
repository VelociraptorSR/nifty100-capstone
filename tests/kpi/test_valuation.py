"""Unit tests for src/analytics/valuation.py — Sprint 4, Day 26."""

import pandas as pd

from src.analytics.valuation import compute_fcf_yield, apply_valuation_flag


def test_fcf_yield_normal_case():
    row = pd.Series({"free_cash_flow_cr": 100, "market_cap_crore": 1000})
    assert compute_fcf_yield(row) == 10.0


def test_fcf_yield_zero_market_cap_returns_none():
    row = pd.Series({"free_cash_flow_cr": 100, "market_cap_crore": 0})
    assert compute_fcf_yield(row) is None


def test_fcf_yield_negative_fcf_is_valid():
    row = pd.Series({"free_cash_flow_cr": -50, "market_cap_crore": 1000})
    assert compute_fcf_yield(row) == -5.0


def test_valuation_flag_caution_above_150pct_of_median():
    assert apply_valuation_flag(pe_ratio=30, sector_median_pe=15) == "Caution"


def test_valuation_flag_discount_below_70pct_of_median():
    assert apply_valuation_flag(pe_ratio=8, sector_median_pe=15) == "Discount"


def test_valuation_flag_fair_within_range():
    assert apply_valuation_flag(pe_ratio=16, sector_median_pe=15) == "Fair"


def test_valuation_flag_unknown_when_median_missing():
    assert apply_valuation_flag(pe_ratio=16, sector_median_pe=None) == "Unknown"