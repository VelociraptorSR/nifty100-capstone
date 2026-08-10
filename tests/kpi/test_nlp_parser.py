"""Unit tests for src/nlp/parser.py — Sprint 5, Day 29."""

import pandas as pd

from src.nlp.parser import parse_growth_text


def test_parse_normal_case():
    assert parse_growth_text("10 Years: 21%") == (10, 21.0)


def test_parse_no_colon():
    assert parse_growth_text("5 Years          14%") == (5, 14.0)


def test_parse_negative_value():
    assert parse_growth_text("5 Years: -12%") == (5, -12.0)


def test_parse_singular_year():
    assert parse_growth_text("1 Year: -2%") == (1, -2.0)


def test_parse_ttm_does_not_match():
    assert parse_growth_text("TTM: 47%") == (None, None)


def test_parse_last_year_does_not_match():
    assert parse_growth_text("Last Year: 17%") == (None, None)


def test_parse_missing_value_returns_none():
    assert parse_growth_text(None) == (None, None)


def test_parse_nan_returns_none():
    assert parse_growth_text(float("nan")) == (None, None)