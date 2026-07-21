"""Unit tests for src/analytics/cagr.py — CAGR engine. Sprint 2, Day 10."""

import pandas as pd
import pytest

from src.analytics.cagr import compute_cagr, compute_company_cagr


def test_cagr_normal_growth():
    cagr, flag = compute_cagr(100, 161, 5)
    assert cagr == pytest.approx(10.0, rel=1e-2)
    assert flag is None


def test_cagr_normal_returns_correct_value():
    cagr, flag = compute_cagr(100, 200, 5)
    assert cagr == pytest.approx(14.87, rel=1e-3)
    assert flag is None


def test_cagr_decline_to_loss():
    cagr, flag = compute_cagr(100, -50, 5)
    assert cagr is None
    assert flag == "DECLINE_TO_LOSS"


def test_cagr_turnaround():
    cagr, flag = compute_cagr(-100, 200, 5)
    assert cagr is None
    assert flag == "TURNAROUND"


def test_cagr_both_negative():
    cagr, flag = compute_cagr(-100, -50, 5)
    assert cagr is None
    assert flag == "BOTH_NEGATIVE"


def test_cagr_zero_base():
    cagr, flag = compute_cagr(0, 200, 5)
    assert cagr is None
    assert flag == "ZERO_BASE"


def test_cagr_insufficient_none_start():
    cagr, flag = compute_cagr(None, 200, 5)
    assert cagr is None
    assert flag == "INSUFFICIENT"


def test_cagr_insufficient_none_end():
    cagr, flag = compute_cagr(100, None, 5)
    assert cagr is None
    assert flag == "INSUFFICIENT"


def test_company_cagr_missing_start_year_is_insufficient():
    df = pd.DataFrame({
        "year": ["2022-03", "2023-03", "2024-03"],
        "sales": [100, 110, 120],
    })
    cagr, flag = compute_company_cagr(df, "sales", "2024-03", 5)
    assert cagr is None
    assert flag == "INSUFFICIENT"


def test_company_cagr_excludes_ttm_row():
    df = pd.DataFrame({
        "year": ["2019-03", "2024-03", "TTM"],
        "sales": [100, 150, 999],
    })
    cagr, flag = compute_company_cagr(df, "sales", "2024-03", 5)
    assert flag is None
    assert cagr == pytest.approx(8.45, rel=1e-2)