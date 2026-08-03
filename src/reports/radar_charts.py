"""Radar Chart Generator — Sprint 3, Day 19.

Generates an 8-axis radar chart per company, overlaying the company's
peer group average. For companies with no peer group, generates a
standalone chart against the Nifty 100 universe average instead.
"""

import os
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

DB_PATH = "data/nifty100.db"
OUTPUT_DIR = "reports/radar_charts"

AXES = [
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
    "composite_quality_score",
]

AXIS_LABELS = ["ROE", "ROCE", "NPM", "D/E Score", "FCF Score", "PAT CAGR 5yr", "Revenue CAGR 5yr", "Composite"]

INVERTED_AXES = {"debt_to_equity"}

def get_normalized_axis_values(conn, dataset):
    """Normalise all 8 axis metrics to 0-100 scale across the given dataset."""
    from src.analytics.ratio_engine import winsorize_and_score

    df = dataset.copy()
    normalized = pd.DataFrame(index=df.index)
    normalized["company_id"] = df["company_id"].values

    for metric in AXES:
        if metric == "composite_quality_score":
            normalized[metric] = df[metric].fillna(df[metric].median())
            continue

        values = df[metric].fillna(df[metric].median())
        if metric in INVERTED_AXES:
            values = -values
        normalized[metric] = winsorize_and_score(values).values

    return normalized

def draw_radar_chart(company_id, company_values, peer_avg_values, output_path, peer_group_label="Peer Group"):
    """Draw one radar chart: company as filled polygon, peer average as
    dashed outline overlay.
    """
    num_axes = len(AXIS_LABELS)
    angles = np.linspace(0, 2 * np.pi, num_axes, endpoint=False).tolist()
    angles += angles[:1]

    company_plot_values = company_values + company_values[:1]
    peer_plot_values = peer_avg_values + peer_avg_values[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))

    ax.plot(angles, company_plot_values, color="#1f77b4", linewidth=2, label=company_id)
    ax.fill(angles, company_plot_values, color="#1f77b4", alpha=0.25)

    ax.plot(angles, peer_plot_values, color="#ff7f0e", linewidth=2, linestyle="dashed", label=peer_group_label)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(AXIS_LABELS, fontsize=10)
    ax.set_ylim(0, 100)
    ax.set_title(f"{company_id} vs {peer_group_label}", fontsize=14, pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    plt.close(fig)
    
def generate_all_radar_charts(conn):
    """Generate radar charts for all 92 companies.

    Companies with a peer group get their peer group average overlay.
    Companies without one get the Nifty 100 universe average instead.
    """
    from src.screener.engine import build_screener_dataset

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    dataset = build_screener_dataset(conn)
    normalized = get_normalized_axis_values(conn, dataset)

    peer_groups = pd.read_sql("SELECT peer_group_name, company_id FROM peer_groups", conn)

    nifty_avg_values = [normalized[m].mean() for m in AXES]

    generated = []
    for _, row in normalized.iterrows():
        company_id = row["company_id"]
        company_values = [row[m] for m in AXES]

        company_peer_groups = peer_groups[peer_groups["company_id"] == company_id]["peer_group_name"]

        if len(company_peer_groups) > 0:
            group_name = company_peer_groups.iloc[0]
            group_members = peer_groups[peer_groups["peer_group_name"] == group_name]["company_id"]
            group_data = normalized[normalized["company_id"].isin(group_members)]
            peer_avg_values = [group_data[m].mean() for m in AXES]
            peer_label = group_name
        else:
            peer_avg_values = nifty_avg_values
            peer_label = "Nifty 100 Avg"

        output_path = f"{OUTPUT_DIR}/{company_id}_radar.png"
        draw_radar_chart(company_id, company_values, peer_avg_values, output_path, peer_group_label=peer_label)
        generated.append(company_id)

    return generated