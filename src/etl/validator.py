"""Data Quality validator for the Nifty 100 ETL pipeline.

Implements DQ-01 through DQ-16 per Section 14 of the project spec.
Each check_dq_XX() function returns a list of violation dicts.
"""

import pandas as pd


def _violation(rule_id, severity, company_id, year, field, issue):
    """Build one standard violation record."""
    return {
        "rule_id": rule_id,
        "severity": severity,
        "company_id": company_id,
        "year": year,
        "field": field,
        "issue": issue,
    }


def check_dq01_company_pk_uniqueness(companies_df):
    """DQ-01: companies.id must be unique. CRITICAL."""
    violations = []
    dupes = companies_df[companies_df["id"].duplicated(keep=False)]
    for _, row in dupes.iterrows():
        violations.append(_violation(
            "DQ-01", "CRITICAL", row["id"], None, "id",
            "Duplicate company ticker (PK) found in companies table"
        ))
    return violations


def check_dq02_annual_pk_uniqueness(df, table_name):
    """DQ-02: no duplicate (company_id, year) pairs in time-series tables. CRITICAL."""
    violations = []
    dupes = df[df.duplicated(subset=["company_id", "year"], keep=False)]
    for _, row in dupes.iterrows():
        violations.append(_violation(
            "DQ-02", "CRITICAL", row["company_id"], row["year"],
            "company_id+year",
            f"Duplicate (company_id, year) pair in {table_name}"
        ))
    return violations


def check_dq03_fk_integrity(child_df, companies_df, table_name):
    """DQ-03: every company_id in a child table must exist in companies.id. CRITICAL."""
    violations = []
    valid_ids = set(companies_df["id"])
    orphans = child_df[~child_df["company_id"].isin(valid_ids)]
    for _, row in orphans.iterrows():
        violations.append(_violation(
            "DQ-03", "CRITICAL", row["company_id"], row.get("year"),
            "company_id",
            f"Orphan company_id in {table_name} — no matching row in companies table"
        ))
    return violations


def exclude_orphan_rows(child_df, companies_df, table_name):
    """DQ-03 remediation: reject rows whose company_id has no match in companies.

    Returns (clean_df, exclusion_log).
    """
    valid_ids = set(companies_df["id"])
    orphan_mask = ~child_df["company_id"].isin(valid_ids)
    orphans = child_df[orphan_mask]

    exclusion_log = []
    for _, row in orphans.iterrows():
        exclusion_log.append(_violation(
            "DQ-03", "CRITICAL", row["company_id"], row.get("year"),
            "company_id",
            f"Excluded orphan row from {table_name} — company_id not in master companies table"
        ))

    clean_df = child_df[~orphan_mask].reset_index(drop=True)
    return clean_df, exclusion_log


def deduplicate_documents(documents_df):
    """DQ-02 remediation, specialised for documents table.

    Unlike deduplicate_annual_table() which blindly keeps the last row,
    this prefers the row with a non-null Annual_Report URL when a
    (company_id, Year) duplicate exists — since these duplicates are
    typically a blank placeholder row alongside a completed one.
    """
    df = documents_df.copy()
    df["_has_url"] = df["Annual_Report"].notna()
    df = df.sort_values("_has_url", ascending=True)

    dupes_mask = df.duplicated(subset=["company_id", "Year"], keep="last")
    removed = df[dupes_mask]

    dedup_log = []
    for _, row in removed.iterrows():
        dedup_log.append(_violation(
            "DQ-02", "CRITICAL", row["company_id"], row["Year"],
            "company_id+Year",
            "Removed duplicate documents row (kept the one with a valid URL)"
        ))

    clean_df = df[~dupes_mask].drop(columns=["_has_url"]).reset_index(drop=True)
    return clean_df, dedup_log


def deduplicate_financial_ratios(fr_df):
    """DQ-02 remediation, specialised for financial_ratios table.

    Some duplicate (company_id, year) rows here have genuinely conflicting
    values (not identical copies) — most commonly in cash_from_operations_cr.
    Since this table is provisional (overwritten by the Sprint 2 Ratio Engine),
    we keep the first occurrence and log the conflicting value for transparency
    rather than attempting to guess which is correct.
    """
    df = fr_df.copy()
    dupes_mask = df.duplicated(subset=["company_id", "year"], keep="first")
    removed = df[dupes_mask]

    dedup_log = []
    for _, row in removed.iterrows():
        dedup_log.append(_violation(
            "DQ-02", "CRITICAL", row["company_id"], row["year"],
            "company_id+year",
            f"Removed conflicting duplicate row from financial_ratios "
            f"(kept first occurrence; dropped row had "
            f"cash_from_operations_cr={row['cash_from_operations_cr']})"
        ))

    clean_df = df[~dupes_mask].reset_index(drop=True)
    return clean_df, dedup_log


def flag_conflicting_duplicates(df, table_name, value_columns, keep="first"):
    """Detect duplicate (company_id, year) rows where VALUES genuinely
    disagree (not just exact copies) — a more serious issue than simple
    duplication, since we cannot algorithmically determine which row is
    correct. Logs as CRITICAL and removes only the conflicting rows
    (keeping one per group), leaving simple identical duplicates
    untouched for deduplicate_annual_table() to handle separately.
    """
    df = df.copy()
    dupe_groups = df[df.duplicated(subset=["company_id", "year"], keep=False)]

    violations = []
    conflicting_keys = set()

    for (cid, year), group in dupe_groups.groupby(["company_id", "year"]):
        distinct_value_sets = group[value_columns].drop_duplicates()
        if len(distinct_value_sets) > 1:
            conflicting_keys.add((cid, year))
            violations.append(_violation(
                "DQ-02-CONFLICT", "CRITICAL", cid, year,
                "+".join(value_columns),
                f"UNRESOLVED CONFLICT in {table_name}: {len(group)} rows for "
                f"({cid}, {year}) have genuinely different values across "
                f"{value_columns} — cannot auto-resolve, needs manual review "
                f"against source. Kept '{keep}' occurrence arbitrarily."
            ))

    if not conflicting_keys:
        return df, violations

    is_conflicting = df.apply(lambda row: (row["company_id"], row["year"]) in conflicting_keys, axis=1)
    conflicting_rows = df[is_conflicting]
    non_conflicting_rows = df[~is_conflicting]

    dupes_mask = conflicting_rows.duplicated(subset=["company_id", "year"], keep=keep)
    resolved_conflicting = conflicting_rows[~dupes_mask]

    clean_df = pd.concat([non_conflicting_rows, resolved_conflicting]).sort_index().reset_index(drop=True)
    return clean_df, violations


def deduplicate_annual_table(df, table_name):
    """DQ-02 remediation: remove duplicate (company_id, year) rows.

    Keeps the last occurrence, per Section 14 spec. Returns
    (clean_df, dedup_log) where dedup_log lists what was removed.
    """
    dupes_mask = df.duplicated(subset=["company_id", "year"], keep="last")
    removed = df[dupes_mask]

    dedup_log = []
    for _, row in removed.iterrows():
        dedup_log.append(_violation(
            "DQ-02", "CRITICAL", row["company_id"], row["year"],
            "company_id+year",
            f"Removed duplicate row from {table_name} (kept last occurrence)"
        ))

    clean_df = df[~dupes_mask].reset_index(drop=True)
    return clean_df, dedup_log



def check_dq07_year_format(df, table_name):
    """DQ-07: year must match YYYY-MM after normalisation. CRITICAL.
    (TTM is treated as a valid special case, not a failure.)
    """
    violations = []
    bad_rows = df[df["year"] == "PARSE_ERROR"]
    for _, row in bad_rows.iterrows():
        violations.append(_violation(
            "DQ-07", "CRITICAL", row["company_id"], row["year"],
            "year",
            f"Unparseable year value in {table_name} — row rejected"
        ))
    return violations


def check_dq08_ticker_format(df, id_column, table_name):
    """DQ-08: company_id must be 2-12 chars after normalisation. CRITICAL."""
    violations = []
    bad_rows = df[df[id_column].isna()]
    for _, row in bad_rows.iterrows():
        violations.append(_violation(
            "DQ-08", "CRITICAL", None, row.get("year"),
            id_column,
            f"Invalid/missing ticker in {table_name} — row rejected"
        ))
    return violations


def check_dq04_balance_sheet_balance(bs_df):
    """DQ-04: |total_assets - total_liabilities| / total_assets < 0.01. WARNING."""
    violations = []
    for _, row in bs_df.iterrows():
        assets = row["total_assets"]
        liabilities = row["total_liabilities"]
        if assets == 0 or pd.isna(assets) or pd.isna(liabilities):
            continue
        diff_pct = abs(assets - liabilities) / assets
        if diff_pct >= 0.01:
            violations.append(_violation(
                "DQ-04", "WARNING", row["company_id"], row["year"],
                "total_assets/total_liabilities",
                f"Balance sheet imbalance: assets={assets}, liabilities={liabilities}, diff={diff_pct:.2%}"
            ))
    return violations


def check_dq05_opm_crosscheck(pl_df, sectors_df):
    """DQ-05: |opm_percentage - computed OPM| < 1.0. WARNING.

    Financials sector is excluded — bank/NBFC income statements are
    structured differently (interest income vs sales), so the standard
    OPM formula produces meaningless extreme values for them.
    """
    violations = []
    financial_ids = set(sectors_df[sectors_df["broad_sector"] == "Financials"]["company_id"])

    for _, row in pl_df.iterrows():
        if row["company_id"] in financial_ids:
            continue

        sales = row["sales"]
        op_profit = row["operating_profit"]
        opm_stated = row["opm_percentage"]
        if sales in (0, None) or pd.isna(sales) or pd.isna(op_profit) or pd.isna(opm_stated):
            continue
        opm_computed = (op_profit / sales) * 100
        diff = abs(opm_stated - opm_computed)
        if diff >= 1.0:
            violations.append(_violation(
                "DQ-05", "WARNING", row["company_id"], row["year"],
                "opm_percentage",
                f"OPM mismatch: stated={opm_stated:.2f}%, computed={opm_computed:.2f}%, diff={diff:.2f}"
            ))
    return violations


def check_dq06_positive_sales(pl_df):
    """DQ-06: sales > 0 for all non-bank companies. WARNING."""
    violations = []
    bad_rows = pl_df[(pl_df["sales"] <= 0) & pl_df["sales"].notna()]
    for _, row in bad_rows.iterrows():
        violations.append(_violation(
            "DQ-06", "WARNING", row["company_id"], row["year"],
            "sales",
            f"Non-positive sales value: {row['sales']}"
        ))
    return violations


def check_dq09_net_cash_check(cf_df):
    """DQ-09: |net_cash_flow - (CFO+CFI+CFF)| <= 10 Cr tolerance. WARNING."""
    violations = []
    for _, row in cf_df.iterrows():
        cfo = row["operating_activity"]
        cfi = row["investing_activity"]
        cff = row["financing_activity"]
        stated_net = row["net_cash_flow"]
        if any(pd.isna(x) for x in [cfo, cfi, cff, stated_net]):
            continue
        computed_net = cfo + cfi + cff
        diff = abs(stated_net - computed_net)
        if diff > 10:
            violations.append(_violation(
                "DQ-09", "WARNING", row["company_id"], row["year"],
                "net_cash_flow",
                f"Net cash flow mismatch: stated={stated_net}, computed={computed_net:.1f}, diff={diff:.1f} Cr"
            ))
    return violations


def check_dq10_nonneg_fixed_assets(bs_df):
    """DQ-10: fixed_assets >= 0. WARNING."""
    violations = []
    bad_rows = bs_df[(bs_df["fixed_assets"] < 0) & bs_df["fixed_assets"].notna()]
    for _, row in bad_rows.iterrows():
        violations.append(_violation(
            "DQ-10", "WARNING", row["company_id"], row["year"],
            "fixed_assets",
            f"Negative fixed_assets: {row['fixed_assets']} (coerced to 0)"
        ))
    return violations


def check_dq11_tax_rate_range(pl_df):
    """DQ-11: 0 <= tax_percentage <= 60. WARNING."""
    violations = []
    bad_rows = pl_df[
        pl_df["tax_percentage"].notna()
        & ((pl_df["tax_percentage"] < 0) | (pl_df["tax_percentage"] > 60))
    ]
    for _, row in bad_rows.iterrows():
        violations.append(_violation(
            "DQ-11", "WARNING", row["company_id"], row["year"],
            "tax_percentage",
            f"Tax rate out of expected range: {row['tax_percentage']}%"
        ))
    return violations


def check_dq12_dividend_payout_cap(pl_df):
    """DQ-12: dividend_payout <= 200%. WARNING."""
    violations = []
    bad_rows = pl_df[pl_df["dividend_payout"].notna() & (pl_df["dividend_payout"] > 200)]
    for _, row in bad_rows.iterrows():
        violations.append(_violation(
            "DQ-12", "WARNING", row["company_id"], row["year"],
            "dividend_payout",
            f"Dividend payout exceeds 200%: {row['dividend_payout']}%"
        ))
    return violations


def check_dq14_eps_sign_consistency(pl_df):
    """DQ-14: eps > 0 if net_profit > 0. WARNING."""
    violations = []
    bad_rows = pl_df[
        pl_df["net_profit"].notna() & pl_df["eps"].notna()
        & (pl_df["net_profit"] > 0) & (pl_df["eps"] <= 0)
    ]
    for _, row in bad_rows.iterrows():
        violations.append(_violation(
            "DQ-14", "WARNING", row["company_id"], row["year"],
            "eps",
            f"EPS sign mismatch: net_profit={row['net_profit']} (positive) but eps={row['eps']}"
        ))
    return violations


def check_dq16_coverage(df, table_name, min_years=5):
    """DQ-16: each company should have >= 5 years of records. WARNING."""
    violations = []
    counts = df[df["year"] != "TTM"].groupby("company_id").size()
    short_companies = counts[counts < min_years]
    for company_id, count in short_companies.items():
        violations.append(_violation(
            "DQ-16", "WARNING", company_id, None,
            "year_coverage",
            f"Only {count} years of {table_name} history (< {min_years} minimum)"
        ))
    return violations


import requests


def check_dq13_url_validity(documents_df, sample_size=None, timeout=5):
    """DQ-13: validate Annual_Report URLs. WARNING.

    Uses requests.head() for speed. Note: BSE India blocks automated
    (non-browser) requests with HTTP 403 even for valid, working PDFs
    — confirmed by manual browser testing. 403 responses are logged
    separately as 'likely bot-blocked, not necessarily broken' rather
    than treated as a confirmed dead link.
    """
    violations = []
    df = documents_df.dropna(subset=["Annual_Report"])
    df = df[~df["Annual_Report"].astype(str).str.strip().str.lower().eq("null")]

    if sample_size is not None:
        df = df.sample(n=min(sample_size, len(df)), random_state=42)

    for _, row in df.iterrows():
        url = row["Annual_Report"]
        if not str(url).startswith(("http://", "https://")):
            violations.append(_violation(
                "DQ-13", "WARNING", row["company_id"], row.get("Year"),
                "Annual_Report",
                f"Malformed URL (missing http/https prefix): {url}"
            ))
            continue
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            if response.status_code == 403:
                violations.append(_violation(
                    "DQ-13", "INFO", row["company_id"], row.get("Year"),
                    "Annual_Report",
                    f"URL returned 403 (likely bot-blocked by server, not necessarily broken): {url}"
                ))
            elif response.status_code != 200:
                violations.append(_violation(
                    "DQ-13", "WARNING", row["company_id"], row.get("Year"),
                    "Annual_Report",
                    f"URL returned status {response.status_code}: {url}"
                ))
        except requests.RequestException as e:
            violations.append(_violation(
                "DQ-13", "WARNING", row["company_id"], row.get("Year"),
                "Annual_Report",
                f"URL request failed: {url} ({type(e).__name__})"
            ))

    return violations


def check_dq15_strict_balance_count(bs_df):
    """DQ-15: count rows where total_liabilities == total_assets exactly.

    INFO only — this is a summary statistic for load_audit.csv, not a
    per-row violation list (per Section 14 spec: 'Flag in load_audit only').
    Returns a dict, not a violations list, since it's a counter.
    """
    valid_rows = bs_df.dropna(subset=["total_assets", "total_liabilities"])
    exact_matches = (valid_rows["total_assets"] == valid_rows["total_liabilities"]).sum()
    total_checked = len(valid_rows)

    return {
        "rule_id": "DQ-15",
        "severity": "INFO",
        "exact_balance_matches": int(exact_matches),
        "total_rows_checked": int(total_checked),
        "exact_match_pct": round(exact_matches / total_checked * 100, 2) if total_checked > 0 else 0,
    }
    
    
def run_all_dq_checks(companies, pl, bs, cf, documents, sectors):
    """Run all 16 DQ rules and return combined violations + cleaned data.

    DQ-15 is returned separately as a summary dict (not a violations list)
    since it's an informational counter, not a per-row check.
    """
    all_violations = []

    all_violations += check_dq01_company_pk_uniqueness(companies)

    pl, dedup_log_pl = deduplicate_annual_table(pl, "profitandloss")
    all_violations += dedup_log_pl
    pl, orphan_log_pl = exclude_orphan_rows(pl, companies, "profitandloss")
    all_violations += orphan_log_pl

    bs, dedup_log_bs = deduplicate_annual_table(bs, "balancesheet")
    all_violations += dedup_log_bs
    bs, orphan_log_bs = exclude_orphan_rows(bs, companies, "balancesheet")
    all_violations += orphan_log_bs

    cf_value_cols = ["operating_activity", "investing_activity", "financing_activity", "net_cash_flow"]
    cf, conflict_log_cf = flag_conflicting_duplicates(cf, "cashflow", cf_value_cols, keep="first")
    all_violations += conflict_log_cf
    cf, dedup_log_cf = deduplicate_annual_table(cf, "cashflow")
    all_violations += dedup_log_cf
    cf, orphan_log_cf = exclude_orphan_rows(cf, companies, "cashflow")
    all_violations += orphan_log_cf

    all_violations += check_dq04_balance_sheet_balance(bs)
    all_violations += check_dq05_opm_crosscheck(pl, sectors)
    all_violations += check_dq06_positive_sales(pl)
    all_violations += check_dq07_year_format(pl, "profitandloss")
    all_violations += check_dq08_ticker_format(pl, "company_id", "profitandloss")
    all_violations += check_dq09_net_cash_check(cf)
    all_violations += check_dq10_nonneg_fixed_assets(bs)
    all_violations += check_dq11_tax_rate_range(pl)
    all_violations += check_dq12_dividend_payout_cap(pl)
    all_violations += check_dq13_url_validity(documents, sample_size=50)
    all_violations += check_dq14_eps_sign_consistency(pl)
    all_violations += check_dq16_coverage(pl, "profitandloss")

    dq15_summary = check_dq15_strict_balance_count(bs)

    clean_data = {"companies": companies, "profitandloss": pl, "balancesheet": bs, "cashflow": cf}
    return all_violations, dq15_summary, clean_data


def save_validation_failures(violations, output_path="output/validation_failures.csv"):
    """Write all violations to CSV, per Deliverable D-03."""
    df = pd.DataFrame(violations)
    df.to_csv(output_path, index=False)
    return output_path