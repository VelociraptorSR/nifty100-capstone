"""Unit tests for src/analytics/cashflow_kpis.py — Sprint 2, Day 11."""

import pandas as pd
import pytest

from src.analytics.cashflow_kpis import (
    compute_fcf,
    compute_capex_intensity,
    compute_fcf_conversion_rate,
    compute_cfo_quality_score,
    classify_capital_allocation,
)


def test_fcf_normal_case():
    row = pd.Series({"operating_activity": 100, "investing_activity": -40})
    assert compute_fcf(row) == 60


def test_fcf_negative_is_valid():
    row = pd.Series({"operating_activity": 50, "investing_activity": -100})
    assert compute_fcf(row) == -50


def test_capex_intensity_asset_light():
    row = pd.Series({"sales": 1000, "investing_activity": -20})
    intensity, label = compute_capex_intensity(row)
    assert intensity == 2.0
    assert label == "Asset Light"


def test_capex_intensity_capital_intensive():
    row = pd.Series({"sales": 1000, "investing_activity": -100})
    intensity, label = compute_capex_intensity(row)
    assert intensity == 10.0
    assert label == "Capital Intensive"


def test_fcf_conversion_zero_operating_profit_returns_none():
    row = pd.Series({"operating_activity": 100, "investing_activity": -40, "operating_profit": 0})
    assert compute_fcf_conversion_rate(row) is None


def test_cfo_quality_insufficient_data_returns_none():
    df = pd.DataFrame({
        "year": ["2022-03", "2023-03", "2024-03"],
        "operating_activity": [100, 110, 120],
        "net_profit": [100, 100, 100],
    })
    score, label = compute_cfo_quality_score(df, "2024-03", window=5)
    assert score is None
    assert label == "Insufficient Data"


def test_cfo_quality_high_quality_label():
    df = pd.DataFrame({
        "year": ["2020-03", "2021-03", "2022-03", "2023-03", "2024-03"],
        "operating_activity": [150, 150, 150, 150, 150],
        "net_profit": [100, 100, 100, 100, 100],
    })
    score, label = compute_cfo_quality_score(df, "2024-03", window=5)
    assert score == pytest.approx(1.5)
    assert label == "High Quality"


def test_classify_reinvestor_pattern():
    row = pd.Series({"operating_activity": 100, "investing_activity": -50, "financing_activity": -30})
    cfo_sign, cfi_sign, cff_sign, label = classify_capital_allocation(row, cfo_quality_score=0.7)
    assert (cfo_sign, cfi_sign, cff_sign) == ("+", "-", "-")
    assert label == "Reinvestor"


def test_classify_distress_signal_pattern():
    row = pd.Series({"operating_activity": -50, "investing_activity": 20, "financing_activity": 30})
    cfo_sign, cfi_sign, cff_sign, label = classify_capital_allocation(row)
    assert label == "Distress Signal"


def test_classify_shareholder_returns_requires_high_quality():
    row = pd.Series({"operating_activity": 100, "investing_activity": -50, "financing_activity": -30})
    cfo_sign, cfi_sign, cff_sign, label = classify_capital_allocation(row, cfo_quality_score=1.2)
    assert label == "Shareholder Returns"