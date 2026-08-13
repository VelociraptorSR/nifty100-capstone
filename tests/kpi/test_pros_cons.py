"""Unit tests for src/nlp/pros_cons_generator.py — Sprint 5, Day 30."""

import pandas as pd

from src.nlp.pros_cons_generator import (
    pro_rule_1_high_roe_sustained, pro_rule_3_debt_free, pro_rule_10_roe_improving_3yr,
    con_rule_1_high_de_nonfinancial, con_rule_4_net_loss_latest,
    fallback_pro, fallback_con,
)


def test_pro_rule_1_fires_when_roe_sustained():
    ratios = pd.DataFrame({"return_on_equity_pct": [25, 26, 27]})
    result = pro_rule_1_high_roe_sustained(ratios)
    assert result is not None
    assert result["rule_id"] == "PRO-01"


def test_pro_rule_1_does_not_fire_with_insufficient_history():
    ratios = pd.DataFrame({"return_on_equity_pct": [25, 26]})
    assert pro_rule_1_high_roe_sustained(ratios) is None


def test_pro_rule_3_fires_when_debt_free():
    ratios = pd.DataFrame({"debt_to_equity": [0.5, 0.2, 0]})
    result = pro_rule_3_debt_free(ratios)
    assert result is not None


def test_pro_rule_3_does_not_fire_with_nonzero_debt():
    ratios = pd.DataFrame({"debt_to_equity": [0.5, 0.2, 0.05]})
    assert pro_rule_3_debt_free(ratios) is None


def test_pro_rule_10_fires_on_improving_trend():
    ratios = pd.DataFrame({"return_on_equity_pct": [10, 15, 20]})
    result = pro_rule_10_roe_improving_3yr(ratios)
    assert result is not None


def test_pro_rule_10_does_not_fire_on_declining_trend():
    ratios = pd.DataFrame({"return_on_equity_pct": [20, 15, 10]})
    assert pro_rule_10_roe_improving_3yr(ratios) is None


def test_con_rule_1_excludes_financials_sector():
    ratios = pd.DataFrame({"debt_to_equity": [1.0, 3.0, 5.0]})
    assert con_rule_1_high_de_nonfinancial(ratios, "Financials") is None


def test_con_rule_1_fires_for_non_financial_high_de():
    ratios = pd.DataFrame({"debt_to_equity": [1.0, 3.0, 5.0]})
    result = con_rule_1_high_de_nonfinancial(ratios, "Industrials")
    assert result is not None


def test_con_rule_4_fires_on_net_loss():
    pl = pd.DataFrame({"net_profit": [100, 50, -20]})
    result = con_rule_4_net_loss_latest(pl)
    assert result is not None


def test_con_rule_4_does_not_fire_on_profit():
    pl = pd.DataFrame({"net_profit": [100, 50, 20]})
    assert con_rule_4_net_loss_latest(pl) is None


def test_fallback_pro_handles_empty_ratios():
    empty = pd.DataFrame(columns=["return_on_equity_pct"])
    result = fallback_pro(empty)
    assert result["rule_id"] == "PRO-FALLBACK-NODATA"


def test_fallback_con_handles_empty_ratios():
    empty = pd.DataFrame(columns=["debt_to_equity"])
    result = fallback_con(empty)
    assert result["rule_id"] == "CON-FALLBACK-NODATA"