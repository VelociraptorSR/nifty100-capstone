"""Unit tests for src/etl/normaliser.py — normalize_year and normalize_ticker.

20 tests for normalize_year, 15 for normalize_ticker, per Sprint 1 spec.
"""

from src.etl.normaliser import normalize_ticker, normalize_year


# ---------- normalize_year() tests (20) ----------

def test_year_mar23():
    assert normalize_year("Mar-23") == "2023-03"


def test_year_mar_space_23():
    assert normalize_year("Mar 23") == "2023-03"


def test_year_march_full_name():
    assert normalize_year("March-2023") == "2023-03"


def test_year_plain_4digit():
    assert normalize_year("2023") == "2023-03"


def test_year_fy_prefix():
    assert normalize_year("FY24") == "2024-03"


def test_year_dec22():
    assert normalize_year("Dec-22") == "2022-12"


def test_year_jun23():
    assert normalize_year("Jun-23") == "2023-06"


def test_year_already_normalised():
    assert normalize_year("2023-03") == "2023-03"


def test_year_garbage():
    assert normalize_year("garbage") == "PARSE_ERROR"


def test_year_ttm_uppercase():
    assert normalize_year("TTM") == "TTM"


def test_year_ttm_lowercase():
    assert normalize_year("ttm") == "TTM"


def test_year_none_input():
    assert normalize_year(None) == "PARSE_ERROR"


def test_year_9month_partial_period():
    assert normalize_year("Mar 2016 9m") == "PARSE_ERROR"


def test_year_footnote_noise():
    assert normalize_year("Mar 2023 15") == "PARSE_ERROR"


def test_year_decimal_corruption():
    assert normalize_year("2024.5") == "PARSE_ERROR"


def test_year_jan_short():
    assert normalize_year("Jan-20") == "2020-01"


def test_year_feb_full_name():
    assert normalize_year("February-2021") == "2021-02"


def test_year_nov_short():
    assert normalize_year("Nov-19") == "2019-11"


def test_year_empty_string():
    assert normalize_year("") == "PARSE_ERROR"


def test_year_whitespace_only():
    assert normalize_year("   ") == "PARSE_ERROR"


# ---------- normalize_ticker() tests (15) ----------

def test_ticker_simple():
    assert normalize_ticker("TCS") == "TCS"


def test_ticker_strip_whitespace():
    assert normalize_ticker("  TCS  ") == "TCS"


def test_ticker_lowercase_to_upper():
    assert normalize_ticker("tcs") == "TCS"


def test_ticker_mixed_case():
    assert normalize_ticker("TcS") == "TCS"


def test_ticker_hyphen_preserved():
    assert normalize_ticker("BAJAJ-AUTO") == "BAJAJ-AUTO"


def test_ticker_ampersand_preserved():
    assert normalize_ticker("M&M") == "M&M"


def test_ticker_none_input():
    assert normalize_ticker(None) is None


def test_ticker_too_short():
    assert normalize_ticker("A") is None


def test_ticker_too_long():
    assert normalize_ticker("A" * 13) is None


def test_ticker_min_length_boundary():
    assert normalize_ticker("AB") == "AB"


def test_ticker_max_length_boundary():
    assert normalize_ticker("A" * 12) == "A" * 12


def test_ticker_numeric_input():
    assert normalize_ticker(12345) == "12345"


def test_ticker_leading_space_only():
    assert normalize_ticker("  TCS") == "TCS"


def test_ticker_trailing_space_only():
    assert normalize_ticker("TCS  ") == "TCS"


def test_ticker_lowercase_hyphenated():
    assert normalize_ticker("tata-motors") == "TATA-MOTORS"