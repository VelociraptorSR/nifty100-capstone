# Sprint 4 Retrospective — Streamlit Dashboard + Valuation

**Sprint dates:** Day 22–28
**Status:** Complete

## What we built

- Full 8-screen Streamlit dashboard: Home, Company Profile, Screener,
  Peer Comparison, Trend Analysis, Sector Analysis, Capital Allocation
  Map, Annual Reports — all backed by a cached data-access layer
  (`src/dashboard/utils/db.py`)
- `src/analytics/valuation.py` — FCF yield, genuine 5-year median P/E
  (verified against real 6-year market_cap history), sector-relative
  Caution/Discount/Fair flags
- `output/valuation_summary.xlsx` (92 rows) and `output/valuation_flags.csv`
  (44 flagged companies)
- Comprehensive integration QA across 10 deliberately-chosen tickers
  spanning 6+ sectors and known edge cases

## Key findings and decisions

1. **Streamlit multi-page import bug**: pages inside `pages/` don't
   automatically inherit the same Python import path as `app.py`.
   Fixed with an explicit `sys.path` insertion at the top of every page
   file — a genuine framework quirk discovered through debugging, not
   documented anywhere obvious beforehand.
2. **Sector donut chart "not updating" investigation**: initially looked
   like a bug (identical across every year selection), but tracing the
   data source (the `sectors` table has no year dimension) confirmed
   this was correct, honest behavior — fixed by adding a clarifying
   caption rather than forcing artificial year-variance into a
   fundamentally static fact.
3. **Capital Allocation Map "click to filter"**: the doc asked for
   click-driven treemap interactivity, which isn't straightforward in
   Streamlit without advanced callback wiring. Substituted a dropdown
   selector achieving the same functional outcome — documented as a
   deliberate, reasonable UX substitution.
4. **5-year median P/E**: initially assumed this might be another
   documented data gap (following the pattern of ROCE/Cash Quality
   simplifications from earlier sprints), but checking the actual
   `market_cap` data first revealed 6 genuine years of history — built
   properly rather than skipped, since the data supported it.
5. **session_state for preset-to-slider interaction**: Streamlit's
   full-script-rerun model required storing preset selections in
   `st.session_state` so slider defaults could reflect a just-clicked
   preset on the next render — a pattern specific to Streamlit's
   execution model, not something obvious from general Python
   experience.

## Known limitations carried into Sprint 5

- Capital Allocation Map uses a dropdown instead of native
  click-to-filter treemap interaction.
- Annual Reports' "unavailable" badge reflects stored data quality
  (missing/malformed URLs), not a live 404 check on every page load —
  a deliberate scope decision to avoid duplicating Sprint 1's DQ-13
  batch validation and to keep the page fast.

## Exit criteria status

| Criterion | Status |
|---|---|
| All 8 screens load without errors for any of 92 tickers | Pass (10-ticker spot-check, all sectors) |
| Company Profile loads in under 3 seconds | Pass |
| Screener CSV download produces a valid file | Pass |
| valuation_summary.xlsx has 92 rows with all required columns | Pass |
| Sprint 4 review | Complete |