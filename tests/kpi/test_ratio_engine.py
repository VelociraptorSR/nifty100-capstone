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