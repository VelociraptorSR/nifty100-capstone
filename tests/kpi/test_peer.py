"""Unit tests for src/analytics/peer.py — Sprint 3, Day 18."""

import pandas as pd


def test_percent_rank_highest_value_gets_rank_one():
    series = pd.Series([10, 20, 30, 40, 50])
    ranks = series.rank(pct=True)
    assert ranks.iloc[4] == 1.0
    assert ranks.iloc[0] == 0.2


def test_de_inversion_lowest_value_gets_highest_rank():
    series = pd.Series([0.1, 0.5, 1.0, 2.0, 5.0])
    ranks = series.rank(pct=True)
    inverted = 1 - ranks
    assert inverted.iloc[0] == 0.8
    assert inverted.iloc[4] == 0.0


def test_compute_peer_percentiles_covers_all_peer_group_companies(tmp_path):
    import sqlite3
    from src.analytics.peer import compute_peer_percentiles

    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE peer_groups (peer_group_name TEXT, company_id TEXT)
    """)
    conn.execute("""
        CREATE TABLE financial_ratios (
            company_id TEXT, year TEXT, return_on_equity_pct REAL,
            return_on_capital_employed_pct REAL, net_profit_margin_pct REAL,
            debt_to_equity REAL, free_cash_flow_cr REAL, pat_cagr_5yr REAL,
            revenue_cagr_5yr REAL, eps_cagr_5yr REAL, interest_coverage REAL,
            asset_turnover REAL
        )
    """)
    conn.execute("INSERT INTO peer_groups VALUES ('TestGroup', 'A'), ('TestGroup', 'B')")
    conn.execute("""
        INSERT INTO financial_ratios VALUES
        ('A', '2024-03', 20, 20, 20, 0.5, 100, 10, 10, 10, 5, 1.0),
        ('B', '2024-03', 10, 10, 10, 1.0, 50, 5, 5, 5, 3, 0.5)
    """)
    conn.commit()

    result = compute_peer_percentiles(conn)
    assert set(result["company_id"]) == {"A", "B"}
    conn.close()


def test_company_not_in_any_peer_group_is_absent_not_errored():
    import sqlite3
    from src.analytics.peer import compute_peer_percentiles

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE peer_groups (peer_group_name TEXT, company_id TEXT)")
    conn.execute("""
        CREATE TABLE financial_ratios (
            company_id TEXT, year TEXT, return_on_equity_pct REAL,
            return_on_capital_employed_pct REAL, net_profit_margin_pct REAL,
            debt_to_equity REAL, free_cash_flow_cr REAL, pat_cagr_5yr REAL,
            revenue_cagr_5yr REAL, eps_cagr_5yr REAL, interest_coverage REAL,
            asset_turnover REAL
        )
    """)
    conn.execute("INSERT INTO financial_ratios VALUES ('LONELY', '2024-03', 20, 20, 20, 0.5, 100, 10, 10, 10, 5, 1.0)")
    conn.commit()

    result = compute_peer_percentiles(conn)
    assert "LONELY" not in result["company_id"].values
    assert len(result) == 0
    conn.close()