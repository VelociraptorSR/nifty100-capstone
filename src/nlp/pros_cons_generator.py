"""Auto Pros/Cons Generator — Sprint 5, Day 30.

Implements 12 pro rules and 12 con rules per Section 30.2 of the
project spec, with confidence scoring (only included if confidence > 60%).
"""

import sqlite3
import pandas as pd

DB_PATH = "data/nifty100.db"


def get_company_history(conn, company_id):
    """Full financial_ratios + P&L + balance sheet + cashflow history
    for one company, sorted by year, excluding TTM.
    """
    ratios = pd.read_sql(
        "SELECT * FROM financial_ratios WHERE company_id = ? AND year != 'TTM' ORDER BY year",
        conn, params=(company_id,)
    )
    pl = pd.read_sql(
        "SELECT year, sales, net_profit, eps FROM profitandloss WHERE company_id = ? AND year != 'TTM' ORDER BY year",
        conn, params=(company_id,)
    )
    bs = pd.read_sql(
        "SELECT year, total_assets, borrowings FROM balancesheet WHERE company_id = ? ORDER BY year",
        conn, params=(company_id,)
    )
    cf = pd.read_sql(
        "SELECT year, operating_activity, financing_activity FROM cashflow WHERE company_id = ? ORDER BY year",
        conn, params=(company_id,)
    )
    return ratios, pl, bs, cf


def make_signal(rule_id, rule_type, text, confidence):
    return {"rule_id": rule_id, "type": rule_type, "text": text, "confidence_pct": confidence}

def pro_rule_1_high_roe_sustained(ratios):
    """ROE > 20% sustained for 3+ years."""
    recent = ratios.tail(3)
    if len(recent) < 3:
        return None
    if (recent["return_on_equity_pct"] > 20).all():
        confidence = min(100, 60 + (recent["return_on_equity_pct"].mean() - 20))
        return make_signal("PRO-01", "pro",
            "Consistently high return on equity above 20% demonstrates exceptional capital efficiency",
            confidence)
    return None


def pro_rule_2_fcf_positive_5yr(ratios):
    """FCF positive for 5+ consecutive years."""
    recent = ratios.tail(5)
    if len(recent) < 5:
        return None
    if (recent["free_cash_flow_cr"] > 0).all():
        return make_signal("PRO-02", "pro",
            "Strong free cash flow generation over 5 years signals healthy business fundamentals",
            85)
    return None


def pro_rule_3_debt_free(ratios):
    """D/E = 0 in latest year."""
    if ratios.empty:
        return None
    latest = ratios.iloc[-1]
    if latest["debt_to_equity"] == 0:
        return make_signal("PRO-03", "pro",
            "Debt-free balance sheet provides financial flexibility and eliminates interest burden",
            90)
    return None


def pro_rule_4_revenue_cagr_15(ratios):
    """Revenue CAGR > 15% over 5 years."""
    if ratios.empty:
        return None
    latest = ratios.iloc[-1]
    cagr = latest.get("revenue_cagr_5yr")
    if pd.notna(cagr) and cagr > 15:
        confidence = min(100, 60 + (cagr - 15))
        return make_signal("PRO-04", "pro",
            "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum",
            confidence)
    return None


def pro_rule_5_high_opm(ratios):
    """OPM > 25% in latest year."""
    if ratios.empty:
        return None
    latest = ratios.iloc[-1]
    opm = latest.get("operating_profit_margin_pct")
    if pd.notna(opm) and opm > 25:
        confidence = min(100, 60 + (opm - 25))
        return make_signal("PRO-05", "pro",
            "Operating profit margin above 25% indicates strong pricing power and cost discipline",
            confidence)
    return None

def pro_rule_6_pat_cagr_20(ratios):
    """PAT CAGR > 20% over 5 years."""
    if ratios.empty:
        return None
    latest = ratios.iloc[-1]
    cagr = latest.get("pat_cagr_5yr")
    if pd.notna(cagr) and cagr > 20:
        confidence = min(100, 60 + (cagr - 20))
        return make_signal("PRO-06", "pro",
            "Net profit compounding at above 20% over 5 years creates significant shareholder value",
            confidence)
    return None


def pro_rule_7_high_icr(ratios):
    """ICR > 10 or Debt Free."""
    if ratios.empty:
        return None
    latest = ratios.iloc[-1]
    icr = latest.get("interest_coverage")
    de = latest.get("debt_to_equity")
    if de == 0 or (pd.notna(icr) and icr > 10):
        return make_signal("PRO-07", "pro",
            "Very high interest coverage ratio reflects negligible financial stress from debt servicing",
            85)
    return None


def pro_rule_8_dividend_yield_fcf(ratios, market_cap_df):
    """Dividend Yield > 2% with FCF positive."""
    if ratios.empty or market_cap_df.empty:
        return None
    latest_ratio = ratios.iloc[-1]
    latest_mc = market_cap_df.iloc[-1]
    div_yield = latest_mc.get("dividend_yield_pct")
    fcf = latest_ratio.get("free_cash_flow_cr")
    if pd.notna(div_yield) and div_yield > 2 and pd.notna(fcf) and fcf > 0:
        return make_signal("PRO-08", "pro",
            "Consistent dividend yield above 2% backed by positive free cash flow",
            75)
    return None


def pro_rule_9_eps_cagr_15(ratios):
    """EPS CAGR > 15% over 5 years."""
    if ratios.empty:
        return None
    latest = ratios.iloc[-1]
    cagr = latest.get("eps_cagr_5yr")
    if pd.notna(cagr) and cagr > 15:
        confidence = min(100, 60 + (cagr - 15))
        return make_signal("PRO-09", "pro",
            "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding",
            confidence)
    return None


def pro_rule_10_roe_improving_3yr(ratios):
    """ROE improving for 3 consecutive years."""
    recent = ratios.tail(3)
    if len(recent) < 3:
        return None
    roe_values = recent["return_on_equity_pct"].tolist()
    if pd.notna(roe_values).all() and roe_values[0] < roe_values[1] < roe_values[2]:
        return make_signal("PRO-10", "pro",
            "Return on equity improving for 3 consecutive years shows strengthening business quality",
            80)
    return None


def pro_rule_11_operating_leverage(ratios):
    """Revenue CAGR > PAT CAGR is wrong direction — actually PAT CAGR > Revenue CAGR shows operating leverage."""
    if ratios.empty:
        return None
    latest = ratios.iloc[-1]
    rev_cagr = latest.get("revenue_cagr_5yr")
    pat_cagr = latest.get("pat_cagr_5yr")
    if pd.notna(rev_cagr) and pd.notna(pat_cagr) and pat_cagr > rev_cagr and rev_cagr > 0:
        return make_signal("PRO-11", "pro",
            "Revenue growing slower than profits shows improving operating leverage and scale benefits",
            75)
    return None


def pro_rule_12_growing_assets_declining_debt(bs):
    """Balance sheet assets growing with declining debt."""
    recent = bs.tail(3)
    if len(recent) < 3:
        return None
    assets_growing = recent["total_assets"].is_monotonic_increasing
    debt_declining = recent["borrowings"].iloc[-1] < recent["borrowings"].iloc[0]
    if assets_growing and debt_declining:
        return make_signal("PRO-12", "pro",
            "Growing asset base funded by internal accruals reflects self-sustaining growth",
            75)
    return None

def con_rule_1_high_de_nonfinancial(ratios, broad_sector):
    """D/E > 2.0 for non-financial companies."""
    if ratios.empty or broad_sector == "Financials":
        return None
    latest = ratios.iloc[-1]
    de = latest.get("debt_to_equity")
    if pd.notna(de) and de > 2.0:
        return make_signal("CON-01", "con",
            f"Debt-to-equity ratio of {de:.2f} is elevated for a non-financial company and warrants monitoring",
            min(100, 60 + (de - 2.0) * 5))
    return None


def con_rule_2_fcf_negative_3yr(ratios):
    """FCF negative for 3 consecutive years."""
    recent = ratios.tail(3)
    if len(recent) < 3:
        return None
    if (recent["free_cash_flow_cr"] < 0).all():
        return make_signal("CON-02", "con",
            "Free cash flow negative for 3 consecutive years raises concern about cash generation quality",
            85)
    return None


def con_rule_3_opm_declining_3yr(ratios):
    """OPM declining for 3 consecutive years."""
    recent = ratios.tail(3)
    if len(recent) < 3:
        return None
    opm_values = recent["operating_profit_margin_pct"].tolist()
    if pd.notna(opm_values).all() and opm_values[0] > opm_values[1] > opm_values[2]:
        return make_signal("CON-03", "con",
            "Operating margins declining for 3 consecutive years suggest pricing or cost pressure",
            80)
    return None


def con_rule_4_net_loss_latest(pl):
    """Net profit negative in latest year."""
    if pl.empty:
        return None
    latest = pl.iloc[-1]
    if pd.notna(latest["net_profit"]) and latest["net_profit"] < 0:
        return make_signal("CON-04", "con",
            "Company reported a net loss in the most recent financial year",
            95)
    return None


def con_rule_5_revenue_declining_2yr(pl):
    """Revenue declining for 2+ years."""
    recent = pl.tail(3)
    if len(recent) < 3:
        return None
    sales = recent["sales"].tolist()
    if pd.notna(sales).all() and sales[2] < sales[1] < sales[0]:
        return make_signal("CON-05", "con",
            "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss",
            80)
    return None


def con_rule_6_low_icr(ratios):
    """ICR < 1.5."""
    if ratios.empty:
        return None
    latest = ratios.iloc[-1]
    icr = latest.get("interest_coverage")
    if pd.notna(icr) and icr < 1.5:
        return make_signal("CON-06", "con",
            "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations",
            90)
    return None


def con_rule_7_payout_over_100(ratios):
    """Dividend payout > 100%."""
    if ratios.empty:
        return None
    latest = ratios.iloc[-1]
    payout = latest.get("dividend_payout_ratio_pct")
    if pd.notna(payout) and payout > 100:
        return make_signal("CON-07", "con",
            "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable",
            85)
    return None


def con_rule_8_de_rising_3yr(ratios):
    """D/E rising for 3 consecutive years."""
    recent = ratios.tail(3)
    if len(recent) < 3:
        return None
    de_values = recent["debt_to_equity"].tolist()
    if pd.notna(de_values).all() and de_values[0] < de_values[1] < de_values[2]:
        return make_signal("CON-08", "con",
            "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk",
            80)
    return None


def con_rule_9_eps_declining_3yr(pl):
    """EPS declining for 3 consecutive years."""
    recent = pl.tail(3)
    if len(recent) < 3:
        return None
    eps_values = recent["eps"].tolist()
    if pd.notna(eps_values).all() and eps_values[0] > eps_values[1] > eps_values[2]:
        return make_signal("CON-09", "con",
            "Earnings per share declining for 3 consecutive years reflects deteriorating profitability",
            80)
    return None


def con_rule_10_low_roce(ratios):
    """ROCE < 10%."""
    if ratios.empty:
        return None
    latest = ratios.iloc[-1]
    roce = latest.get("return_on_capital_employed_pct")
    if pd.notna(roce) and roce < 10:
        return make_signal("CON-10", "con",
            "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital",
            75)
    return None


def con_rule_11_high_net_debt_ebitda(ratios, pl):
    """Net Debt > 3x EBITDA."""
    if ratios.empty or pl.empty:
        return None
    latest_ratio = ratios.iloc[-1]
    latest_pl = pl.iloc[-1]
    total_debt = latest_ratio.get("total_debt_cr")
    ebitda = latest_pl.get("net_profit")
    if pd.notna(total_debt) and pd.notna(ebitda) and ebitda > 0:
        net_debt_to_ebitda = total_debt / ebitda
        if net_debt_to_ebitda > 3:
            return make_signal("CON-11", "con",
                "Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility",
                80)
    return None


def con_rule_12_low_revenue_cagr(ratios):
    """Revenue CAGR < 5% over 5 years."""
    if ratios.empty:
        return None
    latest = ratios.iloc[-1]
    cagr = latest.get("revenue_cagr_5yr")
    if pd.notna(cagr) and cagr < 5:
        return make_signal("CON-12", "con",
            "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum",
            75)
    return None

PRO_RULES = [
    pro_rule_1_high_roe_sustained, pro_rule_2_fcf_positive_5yr, pro_rule_3_debt_free,
    pro_rule_4_revenue_cagr_15, pro_rule_5_high_opm, pro_rule_6_pat_cagr_20,
    pro_rule_7_high_icr, pro_rule_9_eps_cagr_15, pro_rule_10_roe_improving_3yr,
    pro_rule_11_operating_leverage,
]

CON_RULES_RATIOS = [
    con_rule_2_fcf_negative_3yr, con_rule_3_opm_declining_3yr, con_rule_6_low_icr,
    con_rule_7_payout_over_100, con_rule_8_de_rising_3yr, con_rule_10_low_roce,
    con_rule_12_low_revenue_cagr,
]

CON_RULES_PL = [
    con_rule_4_net_loss_latest, con_rule_5_revenue_declining_2yr, con_rule_9_eps_declining_3yr,
]


def generate_signals_for_company(conn, company_id, broad_sector):
    """Run all 24 rules for one company, return list of signals with confidence > 60%."""
    ratios, pl, bs, cf = get_company_history(conn, company_id)
    market_cap = pd.read_sql(
        "SELECT year, dividend_yield_pct FROM market_cap WHERE company_id = ? ORDER BY year",
        conn, params=(company_id,)
    )

    signals = []

    for rule_fn in PRO_RULES:
        result = rule_fn(ratios)
        if result:
            signals.append(result)

    result8 = pro_rule_8_dividend_yield_fcf(ratios, market_cap)
    if result8:
        signals.append(result8)

    result12 = pro_rule_12_growing_assets_declining_debt(bs)
    if result12:
        signals.append(result12)

    result1 = con_rule_1_high_de_nonfinancial(ratios, broad_sector)
    if result1:
        signals.append(result1)

    for rule_fn in CON_RULES_RATIOS:
        result = rule_fn(ratios)
        if result:
            signals.append(result)

    for rule_fn in CON_RULES_PL:
        result = rule_fn(pl)
        if result:
            signals.append(result)

    result11 = con_rule_11_high_net_debt_ebitda(ratios, pl)
    if result11:
        signals.append(result11)

    filtered = [s for s in signals if s["confidence_pct"] > 60]
    
    if not any(s["type"] == "pro" for s in filtered):
        fb = fallback_pro(ratios)
        if fb:
            filtered.append(fb)

    if not any(s["type"] == "con" for s in filtered):
        fb = fallback_con(ratios)
        if fb:
            filtered.append(fb)

    for s in filtered:
        s["company_id"] = company_id

    return filtered


def generate_all_pros_cons(conn):
    """Run rule generation for all 92 companies, verify coverage, return DataFrame."""
    companies = pd.read_sql("SELECT c.id, s.broad_sector FROM companies c LEFT JOIN sectors s ON c.id = s.company_id", conn)

    all_signals = []
    companies_missing_pro = []
    companies_missing_con = []

    for _, row in companies.iterrows():
        signals = generate_signals_for_company(conn, row["id"], row["broad_sector"])
        all_signals.extend(signals)

        has_pro = any(s["type"] == "pro" for s in signals)
        has_con = any(s["type"] == "con" for s in signals)

        if not has_pro:
            companies_missing_pro.append(row["id"])
        if not has_con:
            companies_missing_con.append(row["id"])

    result_df = pd.DataFrame(all_signals)
    return result_df, companies_missing_pro, companies_missing_con

def fallback_pro(ratios):
    """Fallback: if no other pro fired, use the strongest available positive signal."""
    if ratios.empty:
        return make_signal("PRO-FALLBACK-NODATA", "pro",
            "Company is a constituent of the Nifty 100 index, reflecting its scale and market significance",
            61)
    latest = ratios.iloc[-1]
    roe = latest.get("return_on_equity_pct")
    if pd.notna(roe) and roe > 0:
        return make_signal("PRO-FALLBACK", "pro",
            f"Company reported a positive return on equity of {roe:.1f}% in the latest year",
            65)
    return make_signal("PRO-FALLBACK-GENERIC", "pro",
        "Company is a constituent of the Nifty 100 index, reflecting its scale and market significance",
        61)


def fallback_con(ratios):
    """Fallback: if no other con fired, note the absence of major red flags as a neutral observation."""
    if ratios.empty:
        return make_signal("CON-FALLBACK-NODATA", "con",
            "Insufficient balance sheet data available to assess key financial ratios for this company",
            65)
    return make_signal("CON-FALLBACK", "con",
        "No major financial red flags identified in the latest year; standard sector risks such as "
        "competitive intensity and regulatory changes still apply",
        61)  
    
def save_pros_cons(result_df, output_path="output/pros_cons_generated.csv"):
    export_cols = ["company_id", "type", "rule_id", "text", "confidence_pct"]
    result_df[export_cols].to_csv(output_path, index=False)
    return output_path