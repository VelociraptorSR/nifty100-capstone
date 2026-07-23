"""Unit tests for src/screener/engine.py — Sprint 3, Day 15."""

import pandas as pd

from src.screener.engine import apply_filters


def make_test_config():
    return {
        "filters": {
            "roe_min": {"column": "return_on_equity_pct", "comparison": "min"},
            "de_max": {"column": "debt_to_equity", "comparison": "max", "skip_for_sector": "Financials"},
            "icr_min": {"column": "interest_coverage", "comparison": "min", "treat_none_as_infinity": True},
        }
    }


def test_roe_min_filter_excludes_below_threshold():
    dataset = pd.DataFrame({
        "company_id": ["A", "B"],
        "return_on_equity_pct": [20, 5],
        "debt_to_equity": [0.5, 0.5],
        "broad_sector": ["IT", "IT"],
        "interest_coverage": [10, 10],
    })
    result = apply_filters(dataset, {"roe_min": 15}, make_test_config())
    assert list(result["company_id"]) == ["A"]


def test_de_max_filter_skips_financials_sector():
    dataset = pd.DataFrame({
        "company_id": ["BANK1", "NONBANK1"],
        "return_on_equity_pct": [20, 20],
        "debt_to_equity": [10, 10],
        "broad_sector": ["Financials", "Industrials"],
        "interest_coverage": [10, 10],
    })
    result = apply_filters(dataset, {"de_max": 1.0}, make_test_config())
    assert list(result["company_id"]) == ["BANK1"]


def test_icr_min_filter_treats_none_as_infinity():
    dataset = pd.DataFrame({
        "company_id": ["DEBTFREE", "LOWICR"],
        "return_on_equity_pct": [20, 20],
        "debt_to_equity": [0, 0.5],
        "broad_sector": ["IT", "IT"],
        "interest_coverage": [None, 1.0],
    })
    result = apply_filters(dataset, {"icr_min": 5.0}, make_test_config())
    assert list(result["company_id"]) == ["DEBTFREE"]


def test_combined_filters_all_must_pass():
    dataset = pd.DataFrame({
        "company_id": ["GOOD", "FAILS_DE", "FAILS_ROE"],
        "return_on_equity_pct": [20, 20, 5],
        "debt_to_equity": [0.5, 2.0, 0.5],
        "broad_sector": ["IT", "IT", "IT"],
        "interest_coverage": [10, 10, 10],
    })
    result = apply_filters(dataset, {"roe_min": 15, "de_max": 1.0}, make_test_config())
    assert list(result["company_id"]) == ["GOOD"]