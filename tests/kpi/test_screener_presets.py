"""Unit tests for preset screeners — Sprint 3, Day 16."""

import pandas as pd

from src.screener.engine import run_preset


def make_test_config():
    return {
        "filters": {
            "roe_min": {"column": "return_on_equity_pct", "comparison": "min"},
            "de_max": {"column": "debt_to_equity", "comparison": "max", "skip_for_sector": "Financials"},
            "fcf_min": {"column": "free_cash_flow_cr", "comparison": "min"},
            "revenue_cagr_5yr_min": {"column": "revenue_cagr_5yr", "comparison": "min"},
        },
        "presets": {
            "quality_compounder": {
                "roe_min": 15, "de_max": 1.0, "fcf_min": 0, "revenue_cagr_5yr_min": 10
            }
        }
    }


def test_quality_compounder_requires_all_conditions():
    dataset = pd.DataFrame({
        "company_id": ["GOOD", "LOW_ROE", "HIGH_DE"],
        "return_on_equity_pct": [20, 5, 20],
        "debt_to_equity": [0.5, 0.5, 5.0],
        "fcf_cr": [100, 100, 100],
        "free_cash_flow_cr": [100, 100, 100],
        "revenue_cagr_5yr": [15, 15, 15],
        "broad_sector": ["IT", "IT", "IT"],
    })
    result = run_preset(dataset, "quality_compounder", make_test_config())
    assert list(result["company_id"]) == ["GOOD"]


def test_quality_compounder_empty_when_none_qualify():
    dataset = pd.DataFrame({
        "company_id": ["A"],
        "return_on_equity_pct": [5],
        "debt_to_equity": [2.0],
        "free_cash_flow_cr": [-10],
        "revenue_cagr_5yr": [2],
        "broad_sector": ["IT"],
    })
    result = run_preset(dataset, "quality_compounder", make_test_config())
    assert len(result) == 0