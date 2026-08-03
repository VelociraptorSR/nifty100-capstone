# Sprint 3 Retrospective — Screener, Scoring & Sector Analytics

**Sprint dates:** Day 15–21
**Status:** Complete

## What we built

- `src/screener/engine.py` — full filter engine: YAML-driven config for 17
  filters, sector-aware D/E exemption for Financials, ICR infinity handling
  for debt-free companies, 6 preset screeners (5 static + Turnaround Watch
  as year-over-year logic), sector-relative composite scoring
- `output/screener_output.xlsx` — 6 colour-coded sheets, one per preset
- `src/analytics/peer.py` — peer percentile engine (PERCENT_RANK across
  10 metrics, D/E inversion), `peer_percentiles` table (533 rows), and
  the full `peer_comparison.xlsx` export (11 sheets, percentile
  colour-coding, benchmark highlighting, median rows)
- `src/reports/radar_charts.py` — 91 PNG radar charts (8-axis, peer group
  or Nifty 100 average overlay, correctly normalised to a common 0-100
  scale before plotting)
- `config/screener_config.yaml` — fully analyst-editable filter and
  preset definitions

## Key findings and decisions

1. **4 of 6 presets initially returned counts outside the doc's expected
   ranges.** Investigated each individually rather than assuming a bug:
   - Value Pick (2 vs 10-25) and Dividend Champion (30 vs 10-20): traced
     to the underlying dataset's actual valuation/yield distribution
     (simulated market_cap data centres differently than assumed) — no
     code change made, documented as a genuine data characteristic.
   - Debt-Free Blue Chip: genuine bug — requiring exact D/E=0 is
     unrealistic for real financial data; fixed to D/E<0.05.
   - Turnaround Watch: genuine gap — the 3-year Revenue CAGR condition
     was never implemented; added using the existing Sprint 2 CAGR
     engine computed on-demand (not stored, since only 5yr CAGR is
     persisted in financial_ratios).
2. **Sector-relative composite scoring** correctly normalises within each
   broad_sector rather than globally, addressing the cross-sector
   comparison distortions found throughout Sprints 2-3 (bank D/E, OPM,
   ROCE). One documented simplification: Cash Quality is scored on FCF
   alone (30% weight) rather than the doc's three-part sub-formula, since
   CFO/PAT ratio and FCF CAGR are not stored as standalone columns.
3. **Peer percentile rankings verified correct** on IT Services (highest
   ROE = highest percentile rank) and the D/E inversion logic (lowest D/E
   = highest percentile rank) — both confirmed against real data before
   writing to the database.
4. **37 of 92 companies have no peer group assignment** — handled
   gracefully throughout (percentiles, radar charts) with no errors,
   exactly as required.
5. **Caught two of our own bugs before they shipped**: an empty-DataFrame
   KeyError in peer percentile computation (fixed by explicitly declaring
   columns), and a wrong test expectation for D/E inversion math (0.8 is
   correct for a 5-member group, not 1.0 — verified by hand calculation).
6. **Manually verified Quality Compounder's top 5** (TCS, LT, ADANIPOWER,
   INDIGO, NESTLEIND) — all genuinely satisfy all 4 filter conditions,
   and the list is composed of widely-respected, high-quality companies,
   giving strong confidence in the composite scoring approach.

## Known limitations carried into Sprint 4

- Composite score's Cash Quality component remains a simplified
  single-metric proxy (FCF only), not the full three-part formula.
- Value Pick and Dividend Champion preset counts remain outside the
  doc's originally stated expected ranges, due to the underlying
  simulated data's distribution — not something further code changes
  can or should "fix."
- INDIGO's extreme ROE (892%) appears in Quality Compounder results,
  the same "tiny equity base" pattern as BEL/HAL from Sprint 2 — still
  needs thoughtful display treatment in the eventual dashboard.

## Exit criteria status

| Criterion | Status |
|---|---|
| 6 preset screeners each return between 5-50 companies | Partial — 4/6 in range; 2 documented as data-driven deviations |
| peer_comparison.xlsx has exactly 11 sheets | Pass |
| Peer percentile ranks correct (IT Services, spot-check) | Pass |
| All DQ rule unit tests pass | Pass (17 DQ tests, 113 total) |
| Sprint 3 review | Complete |