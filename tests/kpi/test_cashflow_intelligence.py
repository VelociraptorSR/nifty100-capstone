"""Unit tests for cash flow intelligence — Sprint 5, Day 31."""

import pandas as pd

from src.analytics.cashflow_kpis import detect_distress_signal, detect_deleveraging


def test_distress_signal_detected():
    row = pd.Series({"operating_activity": -100, "financing_activity": 50})
    assert detect_distress_signal(row) == True


def test_distress_signal_not_detected_positive_cfo():
    row = pd.Series({"operating_activity": 100, "financing_activity": 50})
    assert detect_distress_signal(row) == False


def test_distress_signal_not_detected_negative_cff():
    row = pd.Series({"operating_activity": -100, "financing_activity": -50})
    assert detect_distress_signal(row) == False


def test_deleveraging_detected():
    row = pd.Series({"financing_activity": -50})
    assert detect_deleveraging(row, prev_borrowings=1000, curr_borrowings=800) == True


def test_deleveraging_not_detected_borrowings_rising():
    row = pd.Series({"financing_activity": -50})
    assert detect_deleveraging(row, prev_borrowings=800, curr_borrowings=1000) == False


def test_deleveraging_not_detected_positive_cff():
    row = pd.Series({"financing_activity": 50})
    assert detect_deleveraging(row, prev_borrowings=1000, curr_borrowings=800) == False