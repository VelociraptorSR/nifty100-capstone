# Sprint 1 Retrospective — Data Foundation

**Sprint dates:** Day 01–07
**Status:** Complete

## What we built

- Full project environment (venv, dependencies, folder structure)
- `normalize_year()` and `normalize_ticker()` with 35 passing unit tests
- Excel loaders for all 12 source files (7 core + 5 supplementary)
- 16 Data Quality rules (DQ-01 through DQ-16) plus one custom addition
  (DQ-02-CONFLICT) discovered during manual review
- `nifty100.db` — 12-table SQLite database with enforced primary keys
  and foreign keys (0 violations)
- `load_audit.csv`, `validation_failures.csv`, `exploratory_queries.sql`
  (15 queries) — all required deliverables

## Key data quality findings

1. **ADANIPORTS (P&L)** — 13 fully duplicated rows, safely deduplicated.
2. **8 orphan companies** (ULTRACEMCO, UNIONBANK, UNITDSPR, VBL, VEDL,
   WIPRO, ZYDUSLIFE, ZOMATO) — present in time-series files but missing
   from the companies master list. Excluded pending master list update.
3. **Bank OPM anomalies** — standard OPM formula produces meaningless
   extreme values for Financials sector; excluded from DQ-05 cross-check.
4. **HAL documents duplicate** — one blank placeholder row alongside a
   complete one; resolved by preferring the complete row.
5. **ABB cashflow conflict** — two genuinely different, non-identical
   data series existed under one ticker for the same years. This is
   NOT a simple duplicate; automated dedup could not determine which
   series is correct. Resolved by keeping the first series and logging
   the conflict as CRITICAL for manual review against the original
   source. **This is the most significant unresolved data quality
   question from Sprint 1** and should be raised with whoever supplied
   the raw cashflow.xlsx file.
6. **Trailing newline in company_name** (HEROMOTOCO) — fixed per spec.
7. **PARSE_ERROR rows silently persisting in the database** — found
   during Day 07 wrap-up review. DQ-07 was detecting these correctly
   but the pipeline never actually removed them before insertion. Fixed
   by adding `remove_unparseable_years()` to the load pipeline.

## Known limitations carried into Sprint 2

- **Non-standard fiscal year-ends**: ~10-11% of rows across P&L/BS/CF
  use a year-end other than March (December/June year-ends for specific
  companies, plus some 2024-09 interim snapshots in balance sheet data).
  The Ratio Engine (Sprint 2) must explicitly handle this — CAGR and
  "latest year" calculations should not naively assume every company's
  year column follows the same cadence.
- **TTM rows** (91 in profitandloss) are valid data but not a fixed
  fiscal year — must be explicitly excluded from any year-over-year or
  CAGR calculation.
- **5 null EPS values** in profitandloss — not yet investigated in
  depth; low priority given small count.
- **financial_ratios table** is the pre-computed reference version
  only; will be fully overwritten by Sprint 2's own Ratio Engine.

## Exit criteria status

| Criterion | Status |
|---|---|
| `SELECT COUNT(*) FROM companies` = 92 | Pass |
| `PRAGMA foreign_key_check` → 0 rows | Pass |
| `load_audit.csv` — zero unexplained CRITICAL rejections | Pass |
| 35+ ETL unit tests pass | Pass (52 total) |
| Manual review of 5 companies | Pass — surfaced ABB conflict |
| Sprint review | Complete |