"""Unit tests for sector-relative composite scoring — Sprint 3, Day 17."""

import pandas as pd

from src.screener.engine import compute_sector_relative_composite_score


def test_sector_relative_score_computed_within_sector_only():
    dataset = pd.DataFrame({
        "company_id": ["A", "B", "C", "D"],
        "broad_sector": ["IT", "IT", "Financials", "Financials"],
        "return_on_equity_pct": [30, 10, 30, 10],
        "return_on_capital_employed_pct": [30, 10, 30, 10],
        "net_profit_margin_pct": [20, 10, 20, 10],
        "free_cash_flow_cr": [100, 50, 100, 50],
        "revenue_cagr_5yr": [15, 5, 15, 5],
        "pat_cagr_5yr": [15, 5, 15, 5],
        "debt_to_equity": [0.2, 0.8, 5.0, 15.0],
        "interest_coverage": [10, 5, 3, 1],
    })
    result = compute_sector_relative_composite_score(dataset)

    it_scores = result[result["broad_sector"] == "IT"].set_index("company_id")["sector_composite_score"]
    fin_scores = result[result["broad_sector"] == "Financials"].set_index("company_id")["sector_composite_score"]

    assert it_scores["A"] > it_scores["B"]
    assert fin_scores["C"] > fin_scores["D"]


def test_sector_relative_score_within_valid_range():
    dataset = pd.DataFrame({
        "company_id": ["A", "B", "C"],
        "broad_sector": ["IT", "IT", "IT"],
        "return_on_equity_pct": [30, 20, 10],
        "return_on_capital_employed_pct": [30, 20, 10],
        "net_profit_margin_pct": [20, 15, 10],
        "free_cash_flow_cr": [100, 60, 20],
        "revenue_cagr_5yr": [15, 10, 5],
        "pat_cagr_5yr": [15, 10, 5],
        "debt_to_equity": [0.1, 0.5, 1.0],
        "interest_coverage": [10, 5, 2],
    })
    result = compute_sector_relative_composite_score(dataset)
    assert result["sector_composite_score"].between(0, 100).all()