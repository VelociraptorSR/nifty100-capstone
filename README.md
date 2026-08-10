# Nifty 100 Financial Intelligence Platform

An end-to-end data platform for analyzing 92 Nifty 100 companies — covering ETL, data quality validation, a financial ratio engine, investment screener, peer comparison analytics, and an 8-screen interactive Streamlit dashboard.

**Status:** Sprint 4 of 6 complete (Days 1–28 of 45)

## Quick Start

### 1. Clone and set up the environment

```bash
git clone https://github.com/VelociraptorSR/nifty100-capstone.git
cd nifty100_capstone
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 2. Add source data files

Place the 7 core Excel files in `data/raw/` and the 5 supplementary files in `data/supporting/` (not included in this repo — see `.gitignore`).

### 3. Build the database

```bash
python -m src.etl.init_db
```

This loads and cleans all 12 source files into `data/nifty100.db` (13 tables total, including `peer_percentiles`), applying 16+ data quality rules documented in `output/validation_failures.csv`.

### 4. Compute financial ratios and peer analytics

```bash
python -m src.analytics.test_ratio_engine_manual
python -m src.analytics.test_peer_manual
python -m src.analytics.test_valuation_manual
```

### 5. Run the dashboard

```bash
streamlit run src/dashboard/app.py
```

Opens automatically at `http://localhost:8501`.

### 6. Run the test suite

```bash
pytest tests/ -v
```

120+ tests covering ETL normalization, data quality rules, KPI formulas, CAGR edge cases, screener logic, peer rankings, and valuation calculations.

## Dashboard Screens

| Screen | Description |
|---|---|
| **Home** | 6 KPI tiles (avg ROE, median P/E, median D/E, total companies, median Revenue CAGR, debt-free count), sector breakdown donut chart, top-5 companies by composite score, year selector |
| **Company Profile** | Search any of the 92 companies; view sector info, 6 KPI tiles, 10-year revenue/profit chart, dual-axis ROE/ROCE trend, pros & cons |
| **Screener** | 10 adjustable metric sliders, 6 one-click presets (Quality, Value, Growth, Dividend, Debt-Free, Turnaround), live-updating results table, CSV export |
| **Peer Comparison** | Select any of 11 peer groups, view an interactive radar chart (company vs. group average) and a benchmark-highlighted comparison table |
| **Trend Analysis** | Overlay up to 3 metrics for one company over a 10-year window, with YoY % change annotations |
| **Sector Analysis** | Bubble chart (Revenue vs. ROE, sized by market cap) and median KPI bar chart per sector |
| **Capital Allocation Map** | Treemap of all 92 companies across 8 capital-allocation behavior patterns |
| **Annual Reports** | Search a company and view links to its available annual reports, with unavailable-report badges where data is missing |

## Project Structure

```
data/               Raw and supporting Excel source files, and the SQLite database
db/                 schema.sql — the database blueprint
src/etl/            Excel loaders, data normalizers, 16+ DQ rules, DB initializer
src/analytics/      Ratio engine, CAGR engine, cash flow KPIs, peer rankings, valuation
src/screener/       Filter engine, preset screeners, composite scoring
src/dashboard/      Streamlit app, 8 pages, cached data loader
src/reports/        Radar chart generation
tests/              120+ pytest unit tests
output/             Generated deliverables (Excel, CSV, log files)
reports/            Generated PDF/PNG reports (radar charts)
docs/               Sprint retrospectives and QA notes
config/             screener_config.yaml — analyst-editable filter thresholds
```

## Key Design Decisions

- **Sector-aware analytics throughout**: Banks/NBFCs are exempted from standard D/E leverage flags and OPM cross-checks, since their capital structure and income statement composition differ fundamentally from non-financial companies.
- **`None` vs. `0` semantics**: financial ratios distinguish "genuinely undefined" (e.g., ROE when equity ≤ 0) from "a real, meaningful zero" (e.g., D/E for a debt-free company) — never conflated.
- **Every data quality decision is logged and explained**, not silently applied — see `output/validation_failures.csv` and `output/ratio_edge_cases.log`.

## Documentation

- `docs/sprint1_retro.md` through `docs/sprint4_retro.md` — detailed, honest retrospectives for each sprint, including known limitations.
- `docs/day27_qa_notes.md` — dashboard integration QA findings.

## Tech Stack

Python, pandas, NumPy, SQLite, Streamlit, Plotly, Matplotlib, openpyxl, PyYAML, pytest.
