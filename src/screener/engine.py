"""Screener Filter Engine — Sprint 3, Day 15.

Loads screener_config.yaml and applies threshold filters to a combined
view of financial_ratios, market_cap, and sectors data.
"""

import sqlite3
import yaml
import pandas as pd

DB_PATH = "data/nifty100.db"
CONFIG_PATH = "config/screener_config.yaml"


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def get_latest_year_per_company(df, year_col="year"):
    """Reduce a multi-year DataFrame to just each company's latest year.

    Handles both text fiscal-year labels (e.g. '2024-03') and plain
    integer calendar years (e.g. 2024, as used in market_cap).
    """
    df = df.copy()

    if df[year_col].dtype == object:
        df["_year_sortable"] = df[year_col].str.replace("-", "").astype(int)
    else:
        df["_year_sortable"] = df[year_col]

    idx = df.groupby("company_id")["_year_sortable"].idxmax()
    return df.loc[idx].drop(columns=["_year_sortable"])


def build_screener_dataset(conn):
    """Combine financial_ratios + market_cap + sectors + companies,
    reduced to each company's latest available year.
    """
    ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
    ratios = get_latest_year_per_company(ratios)

    market_cap = pd.read_sql("SELECT * FROM market_cap", conn)
    market_cap = get_latest_year_per_company(market_cap)

    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT id, company_name FROM companies", conn)

    merged = ratios.merge(market_cap.drop(columns=["year"]), on="company_id", how="left")
    merged = merged.merge(sectors, on="company_id", how="left")
    merged = merged.merge(companies, left_on="company_id", right_on="id", how="left")

    return merged


def apply_filters(dataset, active_filters, config):
    """Apply a dict of {filter_name: threshold_value} to the dataset.

    active_filters example: {"roe_min": 15, "de_max": 1.0}
    """
    filters_config = config["filters"]
    result = dataset.copy()

    for filter_name, threshold in active_filters.items():
        if filter_name not in filters_config:
            continue

        rule = filters_config[filter_name]
        column = rule["column"]
        comparison = rule["comparison"]

        if rule.get("skip_for_sector"):
            skip_mask = result["broad_sector"] == rule["skip_for_sector"]
        else:
            skip_mask = pd.Series(False, index=result.index)

        if rule.get("treat_none_as_infinity"):
            values = result[column].fillna(float("inf"))
        else:
            values = result[column]

        if comparison == "min":
            passes = (values >= threshold) | skip_mask
        else:
            passes = (values <= threshold) | skip_mask

        result = result[passes.fillna(False)]
        
        if "composite_quality_score" in result.columns:
            result = result.sort_values("composite_quality_score", ascending=False)

    return result