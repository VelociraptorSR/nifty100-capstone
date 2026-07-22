"""Unit tests for src/analytics/ratio_engine.py — Sprint 2, Day 12."""

import pandas as pd
import pytest

from src.analytics.ratio_engine import compute_book_value_per_share, winsorize_and_score


def test_book_value_per_share_normal_case():
    row = pd.Series({"equity_capital": 100, "reserves": 900, "face_value": 10})
    # num_shares = 100/10 = 10, book value = 1000/10 = 100
    assert compute_book_value_per_share(row) == 100.0


def test_book_value_per_share_zero_face_value_returns_none():
    row = pd.Series({"equity_capital": 100, "reserves": 900, "face_value": 0})
    assert compute_book_value_per_share(row) is None


def test_winsorize_and_score_clips_extremes():
    series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 100])
    scores = winsorize_and_score(series)
    assert scores.min() == 0
    assert scores.max() == 100


def test_winsorize_and_score_handles_equal_p10_p90():
    series = pd.Series([5, 5, 5, 5, 5])
    scores = winsorize_and_score(series)
    assert (scores == 50).all()
    

from src.analytics.ratio_engine import cross_check_roce, cross_check_roe, get_latest_year_ratios


def test_cross_check_roce_detects_anomaly():
    ratios_df = pd.DataFrame({
        "company_id": ["TEST1"],
        "year": ["2024-03"],
        "return_on_capital_employed_pct": [50.0],
    })
    companies_df = pd.DataFrame({
        "id": ["TEST1"],
        "roce_percentage": [10.0],
    })
    anomalies = cross_check_roce(ratios_df, companies_df, threshold=5.0)
    assert len(anomalies) == 1
    assert anomalies[0]["difference"] == 40.0


def test_cross_check_roce_within_threshold_no_anomaly():
    ratios_df = pd.DataFrame({
        "company_id": ["TEST1"],
        "year": ["2024-03"],
        "return_on_capital_employed_pct": [12.0],
    })
    companies_df = pd.DataFrame({
        "id": ["TEST1"],
        "roce_percentage": [10.0],
    })
    anomalies = cross_check_roce(ratios_df, companies_df, threshold=5.0)
    assert len(anomalies) == 0


def test_get_latest_year_ratios_picks_max_year():
    df = pd.DataFrame({
        "company_id": ["TEST1", "TEST1", "TEST1"],
        "year": ["2020-03", "2022-03", "2024-03"],
        "return_on_equity_pct": [10.0, 15.0, 20.0],
    })
    latest = get_latest_year_ratios(df)
    assert len(latest) == 1
    assert latest.iloc[0]["year"] == "2024-03"