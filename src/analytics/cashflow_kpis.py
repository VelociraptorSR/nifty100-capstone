"""Cash Flow KPIs and Capital Allocation classifier.

Sprint 2, Day 11. Computes Free Cash Flow, CFO Quality Score, CapEx
Intensity, FCF Conversion Rate, and the 8-pattern capital allocation
classifier per Section 10, Module 7 of the project spec.
"""

import sqlite3
import pandas as pd

DB_PATH = "data/nifty100.db"


def get_pl_cf_merged(conn):
    """Join profitandloss and cashflow on (company_id, year)."""
    pl = pd.read_sql("SELECT * FROM profitandloss", conn)
    cf = pd.read_sql("SELECT * FROM cashflow", conn)
    merged = pd.merge(pl, cf, on=["company_id", "year"], suffixes=("_pl", "_cf"))
    return merged


def compute_fcf(row):
    """Free Cash Flow = operating_activity + investing_activity.

    Negative FCF is a valid, meaningful result (company is investing
    or burning cash) — never returns None.
    """
    cfo = row["operating_activity"]
    cfi = row["investing_activity"]
    return cfo + cfi


def compute_capex_intensity(row):
    """CapEx Intensity = abs(investing_activity) / sales x 100.

    <3% = Asset Light, 3-8% = Moderate, >8% = Capital Intensive.
    Returns (value, label). None/'N/A' if sales = 0.
    """
    sales = row["sales"]
    cfi = row["investing_activity"]

    if pd.isna(sales) or sales == 0:
        return None, "N/A"

    intensity = abs(cfi) / sales * 100

    if intensity < 3:
        label = "Asset Light"
    elif intensity <= 8:
        label = "Moderate"
    else:
        label = "Capital Intensive"

    return intensity, label


def compute_fcf_conversion_rate(row):
    """FCF Conversion Rate = FCF / operating_profit x 100.

    None if operating_profit = 0.
    """
    fcf = compute_fcf(row)
    op_profit = row["operating_profit"]

    if pd.isna(op_profit) or op_profit == 0:
        return None

    return (fcf / op_profit) * 100

def compute_cfo_quality_score(company_df, current_year, window=5):
    """CFO Quality Score: average(CFO/PAT) over the trailing window years.

    >1.0 = High Quality, 0.5-1.0 = Moderate, <0.5 = Accrual Risk.
    Returns (score, label). None/'Insufficient Data' if PAT = 0 in any
    year of the window, or fewer than `window` years are available.
    """
    clean_df = company_df[company_df["year"] != "TTM"].copy()
    clean_df["year_num"] = clean_df["year"].str[:4].astype(int)

    current_year_num = int(current_year[:4])
    window_years = list(range(current_year_num - window + 1, current_year_num + 1))

    window_df = clean_df[clean_df["year_num"].isin(window_years)]

    if len(window_df) < window:
        return None, "Insufficient Data"

    if (window_df["net_profit"] == 0).any():
        return None, "Insufficient Data"

    ratios = window_df["operating_activity"] / window_df["net_profit"]
    avg_ratio = ratios.mean()

    if avg_ratio > 1.0:
        label = "High Quality"
    elif avg_ratio >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"

    return avg_ratio, label


def classify_capital_allocation(row, cfo_quality_score=None):
    """Classify a company-year into a capital allocation pattern based on
    the sign of (CFO, CFI, CFF), with CFO/PAT quality distinguishing
    Reinvestor from Shareholder Returns within the (+,-,-) pattern.

    Returns (cfo_sign, cfi_sign, cff_sign, pattern_label).
    """
    cfo = row["operating_activity"]
    cfi = row["investing_activity"]
    cff = row["financing_activity"]

    cfo_sign = "+" if cfo >= 0 else "-"
    cfi_sign = "+" if cfi >= 0 else "-"
    cff_sign = "+" if cff >= 0 else "-"

    pattern = (cfo_sign, cfi_sign, cff_sign)

    if pattern == ("+", "-", "-"):
        if cfo_quality_score is not None and cfo_quality_score > 1.0:
            return cfo_sign, cfi_sign, cff_sign, "Shareholder Returns"
        return cfo_sign, cfi_sign, cff_sign, "Reinvestor"

    pattern_labels = {
        ("+", "+", "-"): "Liquidating Assets",
        ("-", "+", "+"): "Distress Signal",
        ("-", "-", "+"): "Growth Funded by Debt",
        ("+", "+", "+"): "Cash Accumulator",
        ("-", "-", "-"): "Pre-Revenue",
        ("+", "-", "+"): "Mixed",
        ("-", "+", "-"): "Mixed",
    }

    return cfo_sign, cfi_sign, cff_sign, pattern_labels.get(pattern, "Mixed")


def generate_capital_allocation_csv(conn, output_path="output/capital_allocation.csv"):
    """Generate the capital_allocation.csv deliverable for all companies."""
    merged = get_pl_cf_merged(conn)
    merged = merged[merged["year"] != "TTM"].reset_index(drop=True)

    records = []
    for company_id in merged["company_id"].unique():
        company_series = merged[merged["company_id"] == company_id]
        for _, row in company_series.iterrows():
            quality_score, _ = compute_cfo_quality_score(company_series, row["year"])
            cfo_sign, cfi_sign, cff_sign, pattern_label = classify_capital_allocation(
                row, cfo_quality_score=quality_score
            )
            records.append({
                "company_id": row["company_id"],
                "year": row["year"],
                "cfo_sign": cfo_sign,
                "cfi_sign": cfi_sign,
                "cff_sign": cff_sign,
                "pattern_label": pattern_label,
            })

    result_df = pd.DataFrame(records)
    result_df.to_csv(output_path, index=False)
    return result_df

def detect_distress_signal(cf_row):
    """Distress Signal: CFO < 0 AND CFF > 0 in latest year
    (raising cash from financing while operations burn cash)."""
    cfo = cf_row["operating_activity"]
    cff = cf_row["financing_activity"]
    if pd.isna(cfo) or pd.isna(cff):
        return False
    return cfo < 0 and cff > 0


def detect_deleveraging(cf_row, prev_borrowings, curr_borrowings):
    """Deleveraging: CFF < 0 AND borrowings declining year-over-year
    (actively paying down debt)."""
    cff = cf_row["financing_activity"]
    if pd.isna(cff) or pd.isna(prev_borrowings) or pd.isna(curr_borrowings):
        return False
    return cff < 0 and curr_borrowings < prev_borrowings

def build_cashflow_intelligence(conn):
    """Assemble the full cashflow_intelligence.xlsx dataset for all companies."""
    pl = pd.read_sql("SELECT * FROM profitandloss WHERE year != 'TTM'", conn)
    bs = pd.read_sql("SELECT * FROM balancesheet", conn)
    cf = pd.read_sql("SELECT * FROM cashflow WHERE year != 'TTM'", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT id, company_name FROM companies", conn)

    merged = pd.merge(pl, bs, on=["company_id", "year"], suffixes=("_pl", "_bs"))
    merged = pd.merge(merged, cf, on=["company_id", "year"], how="left")

    records = []

    for company_id in merged["company_id"].unique():
        company_df = merged[merged["company_id"] == company_id].sort_values("year")
        if company_df.empty:
            continue

        latest = company_df.iloc[-1]

        cfo_quality_score, cfo_quality_label = compute_cfo_quality_score(company_df, latest["year"])
        capex_intensity, capex_label = compute_capex_intensity(latest)
        fcf_conversion = compute_fcf_conversion_rate(latest)

        rev_cagr_5yr = None
        from src.analytics.cagr import compute_company_cagr
        pl_only = company_df[["year", "sales"]]
        fcf_cagr_5yr, _ = compute_company_cagr(
            company_df.assign(fcf_temp=company_df["operating_activity"] + company_df["investing_activity"]),
            "fcf_temp", latest["year"], 5
        )

        distress = detect_distress_signal(latest)

        prev_borrowings = company_df.iloc[-2]["borrowings"] if len(company_df) >= 2 else None
        deleveraging = detect_deleveraging(latest, prev_borrowings, latest["borrowings"])

        cfo_quality_score_final, _ = compute_cfo_quality_score(company_df, latest["year"])

        records.append({
            "company_id": company_id,
            "cfo_quality_score": cfo_quality_score,
            "cfo_quality_label": cfo_quality_label,
            "capex_intensity_pct": capex_intensity,
            "capex_label": capex_label,
            "fcf_cagr_5yr": fcf_cagr_5yr,
            "fcf_conversion_pct": fcf_conversion,
            "distress_flag": distress,
            "deleveraging_flag": deleveraging,
            "latest_cfo": latest["operating_activity"],
            "latest_cff": latest["financing_activity"],
            "latest_net_profit": latest["net_profit"],
        })

    result_df = pd.DataFrame(records)
    result_df = result_df.merge(sectors, on="company_id", how="left")
    result_df = result_df.merge(companies, left_on="company_id", right_on="id", how="left")

    capital_labels = []
    for company_id in result_df["company_id"]:
        company_df = merged[merged["company_id"] == company_id].sort_values("year")
        latest = company_df.iloc[-1]
        score_row = result_df[result_df["company_id"] == company_id].iloc[0]
        _, _, _, label = classify_capital_allocation(latest, cfo_quality_score=score_row["cfo_quality_score"])
        capital_labels.append(label)
    result_df["capital_allocation_label"] = capital_labels
    
    all_companies = pd.read_sql("SELECT id, company_name FROM companies", conn)
    missing_companies = set(all_companies["id"]) - set(result_df["company_id"])

    if missing_companies:
        sectors_lookup = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
        missing_records = []
        for company_id in missing_companies:
            sector_row = sectors_lookup[sectors_lookup["company_id"] == company_id]
            sector = sector_row["broad_sector"].iloc[0] if len(sector_row) > 0 else None
            name_row = all_companies[all_companies["id"] == company_id]
            name = name_row["company_name"].iloc[0] if len(name_row) > 0 else None

            missing_records.append({
                "company_id": company_id, "cfo_quality_score": None,
                "cfo_quality_label": "Insufficient Data", "capex_intensity_pct": None,
                "capex_label": "Insufficient Data", "fcf_cagr_5yr": None,
                "fcf_conversion_pct": None, "distress_flag": False, "deleveraging_flag": False,
                "latest_cfo": None, "latest_cff": None, "latest_net_profit": None,
                "broad_sector": sector, "id": company_id, "company_name": name,
                "capital_allocation_label": "Insufficient Data",
            })
        result_df = pd.concat([result_df, pd.DataFrame(missing_records)], ignore_index=True)


    return result_df

def export_cashflow_intelligence(result_df, output_path="output/cashflow_intelligence.xlsx"):
    export_cols = [
        "company_id", "company_name", "broad_sector", "cfo_quality_score", "cfo_quality_label",
        "capex_intensity_pct", "capex_label", "fcf_cagr_5yr", "fcf_conversion_pct",
        "distress_flag", "deleveraging_flag", "capital_allocation_label",
    ]
    export_cols = [c for c in export_cols if c in result_df.columns]
    result_df[export_cols].to_excel(output_path, index=False)
    return output_path


def export_distress_alerts(result_df, output_path="output/distress_alerts.csv"):
    distressed = result_df[result_df["distress_flag"] == True]
    export_cols = ["company_id", "company_name", "latest_cfo", "latest_cff", "latest_net_profit"]
    export_cols = [c for c in export_cols if c in distressed.columns]
    distressed[export_cols].to_csv(output_path, index=False)
    return output_path, len(distressed)

def export_distress_alerts(result_df, output_path="output/distress_alerts.csv"):
    distressed = result_df[result_df["distress_flag"] == True].copy()
    distressed["note"] = distressed["broad_sector"].apply(
        lambda s: "Caution: negative CFO/positive CFF can be structurally normal for banks/NBFCs "
                  "due to loan disbursement patterns — review individually, not as automatic distress."
        if s == "Financials" else "Standard distress pattern for non-financial company — recommend review."
    )
    export_cols = ["company_id", "company_name", "broad_sector", "latest_cfo", "latest_cff", "latest_net_profit", "note"]
    export_cols = [c for c in export_cols if c in distressed.columns]
    distressed[export_cols].to_csv(output_path, index=False)
    return output_path, len(distressed)

def generate_pattern_distribution(capital_allocation_df):
    """Count of companies in each capital allocation pattern, latest year only."""
    df = capital_allocation_df.copy()
    df["year_sortable"] = df["year"].astype(str).str.replace("-", "").astype(int)
    idx = df.groupby("company_id")["year_sortable"].idxmax()
    latest = df.loc[idx]

    distribution = latest["pattern_label"].value_counts().reset_index()
    distribution.columns = ["pattern_label", "company_count"]
    return distribution, latest

def detect_pattern_changes(capital_allocation_df):
    """Identify companies whose capital allocation pattern changed
    between their two most recent available years.
    """
    df = capital_allocation_df.copy()
    df["year_sortable"] = df["year"].astype(str).str.replace("-", "").astype(int)
    df = df.sort_values(["company_id", "year_sortable"])

    changes = []
    for company_id, group in df.groupby("company_id"):
        if len(group) < 2:
            continue
        previous = group.iloc[-2]
        latest = group.iloc[-1]
        if previous["pattern_label"] != latest["pattern_label"]:
            changes.append({
                "company_id": company_id,
                "from_year": previous["year"],
                "from_pattern": previous["pattern_label"],
                "to_year": latest["year"],
                "to_pattern": latest["pattern_label"],
            })

    return pd.DataFrame(changes, columns=["company_id", "from_year", "from_pattern", "to_year", "to_pattern"])