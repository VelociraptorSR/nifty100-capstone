"""Unit tests for src/etl/validator.py — DQ-01 through DQ-16.

Each test crafts a small DataFrame with a known violation and checks
that the corresponding check_dq_XX function correctly flags it.
"""

import pandas as pd

from src.etl.validator import (
    check_dq01_company_pk_uniqueness,
    check_dq03_fk_integrity,
    check_dq04_balance_sheet_balance,
    check_dq06_positive_sales,
    check_dq09_net_cash_check,
    check_dq10_nonneg_fixed_assets,
    check_dq11_tax_rate_range,
    check_dq12_dividend_payout_cap,
    check_dq14_eps_sign_consistency,
    check_dq16_coverage,
    deduplicate_annual_table,
)


def test_dq01_duplicate_ticker_detected():
    companies = pd.DataFrame({"id": ["TCS", "TCS", "INFY"]})
    violations = check_dq01_company_pk_uniqueness(companies)
    assert len(violations) == 2


def test_dq01_no_duplicates_passes_clean():
    companies = pd.DataFrame({"id": ["TCS", "INFY"]})
    violations = check_dq01_company_pk_uniqueness(companies)
    assert len(violations) == 0


def test_dq02_dedup_removes_exact_duplicate():
    df = pd.DataFrame({
        "company_id": ["TCS", "TCS"],
        "year": ["2023-03", "2023-03"],
    })
    clean_df, log = deduplicate_annual_table(df, "test_table")
    assert len(clean_df) == 1
    assert len(log) == 1


def test_dq03_orphan_row_detected():
    companies = pd.DataFrame({"id": ["TCS", "INFY"]})
    child = pd.DataFrame({"company_id": ["TCS", "FAKECO"], "year": ["2023-03", "2023-03"]})
    violations = check_dq03_fk_integrity(child, companies, "test_table")
    assert len(violations) == 1
    assert violations[0]["company_id"] == "FAKECO"


def test_dq04_bs_balance():
    bs = pd.DataFrame({
        "company_id": ["TCS"], "year": ["2023-03"],
        "total_assets": [1000], "total_liabilities": [1020],
    })
    violations = check_dq04_balance_sheet_balance(bs)
    assert len(violations) == 1


def test_dq04_bs_balance_within_tolerance_passes():
    bs = pd.DataFrame({
        "company_id": ["TCS"], "year": ["2023-03"],
        "total_assets": [1000], "total_liabilities": [1005],
    })
    violations = check_dq04_balance_sheet_balance(bs)
    assert len(violations) == 0


def test_dq06_zero_sales():
    pl = pd.DataFrame({"company_id": ["TCS"], "year": ["2023-03"], "sales": [0]})
    violations = check_dq06_positive_sales(pl)
    assert len(violations) == 1


def test_dq06_positive_sales_passes():
    pl = pd.DataFrame({"company_id": ["TCS"], "year": ["2023-03"], "sales": [1000]})
    violations = check_dq06_positive_sales(pl)
    assert len(violations) == 0


def test_dq09_net_cash_mismatch_detected():
    cf = pd.DataFrame({
        "company_id": ["TCS"], "year": ["2023-03"],
        "operating_activity": [100], "investing_activity": [-50],
        "financing_activity": [-20], "net_cash_flow": [100],
    })
    violations = check_dq09_net_cash_check(cf)
    assert len(violations) == 1


def test_dq10_negative_fixed_assets_detected():
    bs = pd.DataFrame({"company_id": ["TCS"], "year": ["2023-03"], "fixed_assets": [-50]})
    violations = check_dq10_nonneg_fixed_assets(bs)
    assert len(violations) == 1


def test_dq11_tax_rate_out_of_range():
    pl = pd.DataFrame({"company_id": ["TCS"], "year": ["2023-03"], "tax_percentage": [75]})
    violations = check_dq11_tax_rate_range(pl)
    assert len(violations) == 1


def test_dq11_tax_rate_in_range_passes():
    pl = pd.DataFrame({"company_id": ["TCS"], "year": ["2023-03"], "tax_percentage": [25]})
    violations = check_dq11_tax_rate_range(pl)
    assert len(violations) == 0


def test_dq12_dividend_payout_exceeds_cap():
    pl = pd.DataFrame({"company_id": ["TCS"], "year": ["2023-03"], "dividend_payout": [250]})
    violations = check_dq12_dividend_payout_cap(pl)
    assert len(violations) == 1


def test_dq14_eps_sign_mismatch():
    pl = pd.DataFrame({
        "company_id": ["TCS"], "year": ["2023-03"],
        "net_profit": [500], "eps": [-2],
    })
    violations = check_dq14_eps_sign_consistency(pl)
    assert len(violations) == 1


def test_dq14_eps_sign_consistent_passes():
    pl = pd.DataFrame({
        "company_id": ["TCS"], "year": ["2023-03"],
        "net_profit": [500], "eps": [10],
    })
    violations = check_dq14_eps_sign_consistency(pl)
    assert len(violations) == 0


def test_dq16_insufficient_coverage_detected():
    pl = pd.DataFrame({
        "company_id": ["TCS", "TCS"],
        "year": ["2022-03", "2023-03"],
    })
    violations = check_dq16_coverage(pl, "profitandloss", min_years=5)
    assert len(violations) == 1


def test_dq16_sufficient_coverage_passes():
    pl = pd.DataFrame({
        "company_id": ["TCS"] * 6,
        "year": ["2018-03", "2019-03", "2020-03", "2021-03", "2022-03", "2023-03"],
    })
    violations = check_dq16_coverage(pl, "profitandloss", min_years=5)
    assert len(violations) == 0