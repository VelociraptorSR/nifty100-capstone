"""Excel loader for the Nifty 100 ETL pipeline.

Reads the 7 core + 5 supplementary Excel files, applies normalisation,
and returns clean pandas DataFrames ready for validation and DB loading.
"""

import pandas as pd

from src.etl.normaliser import normalize_ticker, normalize_year

RAW_DIR = "data/raw"
SUPPORTING_DIR = "data/supporting"


def load_companies():
    path = f"{RAW_DIR}/companies.xlsx"
    df = pd.read_excel(path, header=1)

    df["id"] = df["id"].apply(normalize_ticker)
    df["company_name"] = df["company_name"].str.split("\n").str[0].str.strip()

    return df


def load_profitandloss():
    """Load profitandloss.xlsx — annual P&L statements.

    Normalises company_id (ticker) and year for every row.
    """
    path = f"{RAW_DIR}/profitandloss.xlsx"
    df = pd.read_excel(path, header=1)

    df["company_id"] = df["company_id"].apply(normalize_ticker)
    df["year"] = df["year"].apply(normalize_year)

    return df


def load_balancesheet():
    """Load balancesheet.xlsx — annual balance sheet statements.

    Normalises company_id (ticker) and year for every row.
    """
    path = f"{RAW_DIR}/balancesheet.xlsx"
    df = pd.read_excel(path, header=1)

    df["company_id"] = df["company_id"].apply(normalize_ticker)
    df["year"] = df["year"].apply(normalize_year)

    return df


def load_cashflow():
    """Load cashflow.xlsx — annual cash flow statements.

    Normalises company_id (ticker) and year for every row.
    """
    path = f"{RAW_DIR}/cashflow.xlsx"
    df = pd.read_excel(path, header=1)

    df["company_id"] = df["company_id"].apply(normalize_ticker)
    df["year"] = df["year"].apply(normalize_year)

    return df


def load_analysis():
    """Load analysis.xlsx — pre-computed growth metrics (partial coverage).

    Normalises company_id only; growth-metric text fields are parsed
    later by the NLP module (Sprint 5).
    """
    path = f"{RAW_DIR}/analysis.xlsx"
    df = pd.read_excel(path, header=1)

    df["company_id"] = df["company_id"].apply(normalize_ticker)

    return df


def load_documents():
    """Load documents.xlsx — annual report URL repository.

    Normalises company_id. Note: the year column is capitalised 'Year'
    in this file (unlike other core files), and is a calendar year,
    not a fiscal year, so it does not need normalize_year().
    """
    path = f"{RAW_DIR}/documents.xlsx"
    df = pd.read_excel(path, header=1)

    df["company_id"] = df["company_id"].apply(normalize_ticker)
    df["Year"] = df["Year"].astype(int)

    return df


def load_prosandcons():
    """Load prosandcons.xlsx — qualitative investment insights (partial coverage).

    Normalises company_id only. Text fields (pros/cons) are used as-is;
    Sprint 3/5 will auto-generate entries for companies missing coverage.
    """
    path = f"{RAW_DIR}/prosandcons.xlsx"
    df = pd.read_excel(path, header=1)

    df["company_id"] = df["company_id"].apply(normalize_ticker)

    return df


def load_sectors():
    """Load sectors.xlsx — company sector mapping (supplementary dataset).

    Note: supplementary files use header=0 (unlike core files, which
    use header=1), per Section 5 of the project spec.
    """
    path = f"{SUPPORTING_DIR}/sectors.xlsx"
    df = pd.read_excel(path, header=0)

    df["company_id"] = df["company_id"].apply(normalize_ticker)

    return df


def load_stock_prices():
    """Load stock_prices.xlsx — simulated monthly OHLCV price history.

    Note: this dataset is SIMULATED, not real market data (per project
    spec Section 6.2) — must be labelled as such wherever displayed.
    """
    path = f"{SUPPORTING_DIR}/stock_prices.xlsx"
    df = pd.read_excel(path, header=0)

    df["company_id"] = df["company_id"].apply(normalize_ticker)

    return df


def load_market_cap():
    """Load market_cap.xlsx — simulated annual valuation multiples.

    Note: this dataset is SIMULATED, not real market data (per project
    spec Section 6.3). 'year' here is a plain calendar year, not a
    fiscal-year label, so normalize_year() is not needed.
    """
    path = f"{SUPPORTING_DIR}/market_cap.xlsx"
    df = pd.read_excel(path, header=0)

    df["company_id"] = df["company_id"].apply(normalize_ticker)

    return df


def load_peer_groups():
    """Load peer_groups.xlsx — manually defined peer comparison groups.

    Normalises company_id for each membership row.
    """
    path = f"{SUPPORTING_DIR}/peer_groups.xlsx"
    df = pd.read_excel(path, header=0)

    df["company_id"] = df["company_id"].apply(normalize_ticker)

    return df


def load_financial_ratios():
    """Load financial_ratios.xlsx — pre-computed KPI table (supplementary).

    Normalises company_id and year. Used for cross-validation against
    the Ratio Engine's own computed values in Sprint 2.
    """
    path = f"{SUPPORTING_DIR}/financial_ratios.xlsx"
    df = pd.read_excel(path, header=0)

    df["company_id"] = df["company_id"].apply(normalize_ticker)
    df["year"] = df["year"].apply(normalize_year)

    return df