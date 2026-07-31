"""Peer Percentile Ranking Engine — Sprint 3, Day 18.

Computes PERCENT_RANK for 10 metrics within each of 11 peer groups,
with D/E inverted (lower is better) per Section 18 of the project spec.
"""

import sqlite3
import pandas as pd

DB_PATH = "data/nifty100.db"

METRICS = [
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
    "eps_cagr_5yr",
    "interest_coverage",
    "asset_turnover",
]

INVERTED_METRICS = {"debt_to_equity"}


def get_latest_year_per_company(df, year_col="year"):
    """Reduce a multi-year DataFrame to just each company's latest year."""
    df = df.copy()
    if df[year_col].dtype == object:
        df["_year_sortable"] = df[year_col].str.replace("-", "").astype(int)
    else:
        df["_year_sortable"] = df[year_col]
    idx = df.groupby("company_id")["_year_sortable"].idxmax()
    return df.loc[idx].drop(columns=["_year_sortable"])


def compute_peer_percentiles(conn):
    """Compute percentile ranks for all 10 metrics within each peer group.

    Returns a DataFrame ready to insert into peer_percentiles.
    Companies not in any peer group are simply absent from the result
    (handled gracefully, not an error).
    """
    ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
    ratios = get_latest_year_per_company(ratios)

    peer_groups = pd.read_sql("SELECT peer_group_name, company_id FROM peer_groups", conn)
    merged = peer_groups.merge(ratios, on="company_id", how="left")

    records = []
    for group_name in merged["peer_group_name"].unique():
        group_df = merged[merged["peer_group_name"] == group_name]

        for metric in METRICS:
            if metric not in group_df.columns:
                continue

            valid = group_df.dropna(subset=[metric])
            if len(valid) == 0:
                continue

            if metric in INVERTED_METRICS:
                ranks = 1 - valid[metric].rank(pct=True)
            else:
                ranks = valid[metric].rank(pct=True)

            for (_, row), pct_rank in zip(valid.iterrows(), ranks):
                records.append({
                    "company_id": row["company_id"],
                    "peer_group_name": group_name,
                    "metric": metric,
                    "value": row[metric],
                    "percentile_rank": pct_rank,
                    "year": row["year"],
                })

    columns = ["company_id", "peer_group_name", "metric", "value", "percentile_rank", "year"]
    return pd.DataFrame(records, columns=columns)

def write_peer_percentiles(conn, percentiles_df):
    """Write computed percentiles into the peer_percentiles table."""
    conn.execute("DELETE FROM peer_percentiles")
    conn.commit()
    percentiles_df.to_sql("peer_percentiles", conn, if_exists="append", index=False)