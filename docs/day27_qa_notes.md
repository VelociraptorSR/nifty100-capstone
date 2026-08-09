# Day 27 — Integration QA Notes

**Sprint 4, Day 27**

## Tickers tested across all 8 screens

TCS (IT), HDFCBANK (Financials), ITC (FMCG), RELIANCE (Energy/Conglomerate),
SUNPHARMA (Healthcare), BEL (Industrials, known extreme ROE/ROCE outlier),
JIOFIN (Financials, only 2 years of history), ADANIGREEN (Energy, high
debt-funded capital structure), NESTLEIND (Consumer Staples), and one
orphan company (not in companies table) to confirm graceful "not found"
handling.

**Result:** all 10 tickers rendered correctly across all 8 screens. No
crashes, no unhandled exceptions.

## Specific edge cases verified

- Partial-year companies (JIOFIN: 2yr, LICI: 6yr) render correctly on
  Trend Analysis without breaking the 10-year chart logic.
- Screener with extreme slider values (max ROE, min D/E) correctly
  returns 0 results without crashing.
- Small peer groups (Life Insurance, Consumer Finance) render correctly
  on the Peer Comparison radar chart and table.
- No chart overflow observed on any screen at standard browser width.
- No stray None/NaN text observed in KPI tiles — all missing values
  correctly display as "N/A".
- Company Profile screen load time comfortably under 3 seconds across
  5 different tickers, consistent with expectations given
  @st.cache_data(ttl=600) on all database access functions.

## Regression check

Full automated test suite (120 tests) re-run after all dashboard work
— 0 failures, confirming no analytics logic was broken by Sprint 4's
dashboard integration.

## Bugs found and fixed during Sprint 4

- Streamlit multi-page `ModuleNotFoundError` for `src` imports — fixed
  with explicit sys.path insertion in every page file (Day 23).