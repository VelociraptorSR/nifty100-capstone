"""Unit tests for capital allocation reporting — Sprint 5, Day 32."""

import pandas as pd

from src.analytics.cashflow_kpis import generate_pattern_distribution, detect_pattern_changes


def test_pattern_distribution_counts_latest_year_only():
    df = pd.DataFrame({
        "company_id": ["A", "A", "B", "B"],
        "year": ["2023-03", "2024-03", "2023-03", "2024-03"],
        "pattern_label": ["Reinvestor", "Mixed", "Mixed", "Mixed"],
    })
    distribution, latest = generate_pattern_distribution(df)
    assert len(latest) == 2
    mixed_count = distribution[distribution["pattern_label"] == "Mixed"]["company_count"].iloc[0]
    assert mixed_count == 2


def test_detect_pattern_changes_finds_genuine_change():
    df = pd.DataFrame({
        "company_id": ["A", "A"],
        "year": ["2023-03", "2024-03"],
        "pattern_label": ["Reinvestor", "Mixed"],
    })
    changes = detect_pattern_changes(df)
    assert len(changes) == 1
    assert changes.iloc[0]["from_pattern"] == "Reinvestor"
    assert changes.iloc[0]["to_pattern"] == "Mixed"


def test_detect_pattern_changes_ignores_unchanged_pattern():
    df = pd.DataFrame({
        "company_id": ["A", "A"],
        "year": ["2023-03", "2024-03"],
        "pattern_label": ["Reinvestor", "Reinvestor"],
    })
    changes = detect_pattern_changes(df)
    assert len(changes) == 0


def test_detect_pattern_changes_skips_single_year_company():
    df = pd.DataFrame({
        "company_id": ["A"],
        "year": ["2024-03"],
        "pattern_label": ["Reinvestor"],
    })
    changes = detect_pattern_changes(df)
    assert len(changes) == 0