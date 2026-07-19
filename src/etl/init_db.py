"""Initialise the SQLite database from db/schema.sql.

Run this script directly to (re)create data/nifty100.db with all tables
defined in the schema file.
"""
import pandas as pd
import sqlite3
import time
from datetime import datetime

DB_PATH = "data/nifty100.db"
SCHEMA_PATH = "db/schema.sql"


def get_connection():
    """Open a SQLite connection with foreign key enforcement explicitly enabled.

    SQLite requires this PRAGMA to be set on every new connection — it is
    not a persistent database-level setting.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    with open(SCHEMA_PATH, "r") as f:
        schema = f.read()
    conn.executescript(schema)
    conn.commit()

    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    conn.close()

    return tables



def insert_companies(conn, companies_df):
    cols = ["id", "company_name", "about_company", "website",
            "face_value", "book_value", "roce_percentage", "roe_percentage"]
    df = companies_df[cols]
    df.to_sql("companies", conn, if_exists="append", index=False)


def insert_sectors(conn, sectors_df):
    cols = ["company_id", "broad_sector", "sub_sector",
            "index_weight_pct", "market_cap_category"]
    df = sectors_df[cols]
    df.to_sql("sectors", conn, if_exists="append", index=False)


def insert_profitandloss(conn, pl_df):
    cols = ["company_id", "year", "sales", "expenses", "operating_profit",
            "opm_percentage", "other_income", "interest", "depreciation",
            "profit_before_tax", "tax_percentage", "net_profit", "eps",
            "dividend_payout"]
    df = pl_df[cols]
    df.to_sql("profitandloss", conn, if_exists="append", index=False)
    
    
def insert_balancesheet(conn, bs_df):
    cols = ["company_id", "year", "equity_capital", "reserves", "borrowings",
            "other_liabilities", "total_liabilities", "fixed_assets", "cwip",
            "investments", "other_asset", "total_assets"]
    df = bs_df[cols]
    df.to_sql("balancesheet", conn, if_exists="append", index=False)


def insert_cashflow(conn, cf_df):
    cols = ["company_id", "year", "operating_activity", "investing_activity",
            "financing_activity", "net_cash_flow"]
    df = cf_df[cols]
    df.to_sql("cashflow", conn, if_exists="append", index=False)


def insert_analysis(conn, analysis_df):
    cols = ["id", "company_id", "compounded_sales_growth", "compounded_profit_growth",
            "stock_price_cagr", "roe"]
    df = analysis_df[cols]
    df.to_sql("analysis", conn, if_exists="append", index=False)


def insert_documents(conn, documents_df):
    df = documents_df.rename(columns={"Year": "year", "Annual_Report": "annual_report"})
    df = df[["company_id", "year", "annual_report"]]
    df.to_sql("documents", conn, if_exists="append", index=False)


def insert_prosandcons(conn, prosandcons_df):
    cols = ["id", "company_id", "pros", "cons"]
    df = prosandcons_df[cols]
    df.to_sql("prosandcons", conn, if_exists="append", index=False)


def insert_stock_prices(conn, sp_df):
    cols = ["company_id", "date", "open_price", "high_price", "low_price",
            "close_price", "volume", "adjusted_close"]
    df = sp_df[cols]
    df.to_sql("stock_prices", conn, if_exists="append", index=False)


def insert_market_cap(conn, mc_df):
    cols = ["company_id", "year", "market_cap_crore", "enterprise_value_crore",
            "pe_ratio", "pb_ratio", "ev_ebitda", "dividend_yield_pct"]
    df = mc_df[cols]
    df.to_sql("market_cap", conn, if_exists="append", index=False)


def insert_financial_ratios(conn, fr_df):
    cols = ["company_id", "year", "net_profit_margin_pct", "operating_profit_margin_pct",
            "return_on_equity_pct", "debt_to_equity", "interest_coverage",
            "asset_turnover", "free_cash_flow_cr", "capex_cr", "earnings_per_share",
            "book_value_per_share", "dividend_payout_ratio_pct", "total_debt_cr",
            "cash_from_operations_cr"]
    df = fr_df[cols]
    df.to_sql("financial_ratios", conn, if_exists="append", index=False)


def insert_peer_groups(conn, pg_df):
    df = pg_df.copy()
    df["is_benchmark"] = df["is_benchmark"].astype(int)
    cols = ["id", "peer_group_name", "company_id", "is_benchmark"]
    df = df[cols]
    df.to_sql("peer_groups", conn, if_exists="append", index=False)


def load_and_track(conn, df, insert_func, table_name, rows_in):
    """Insert a DataFrame into a table while tracking audit metrics.

    Returns one load_audit.csv row as a dict.
    """
    start = time.time()
    insert_func(conn, df)
    conn.commit()
    runtime = time.time() - start

    rows_out = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

    return {
        "table": table_name,
        "rows_in": rows_in,
        "rows_out": rows_out,
        "rejected": rows_in - rows_out,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "runtime_s": round(runtime, 4),
    }


if __name__ == "__main__":
    from src.etl.loader import (
        load_companies, load_sectors, load_profitandloss, load_balancesheet,
        load_cashflow, load_analysis, load_documents, load_prosandcons,
        load_stock_prices, load_market_cap, load_financial_ratios, load_peer_groups,
    )
    from src.etl.validator import (
        deduplicate_annual_table, deduplicate_documents,
        deduplicate_financial_ratios, exclude_orphan_rows,
    )

    tables = init_db()
    print("Tables created:", len(tables))

    conn = get_connection()
    audit_rows = []

    # --- companies (no cleaning needed, it's the master reference) ---
    companies = load_companies()
    audit_rows.append(load_and_track(conn, companies, insert_companies, "companies", len(companies)))

    # --- sectors ---
    sectors = load_sectors()
    audit_rows.append(load_and_track(conn, sectors, insert_sectors, "sectors", len(sectors)))

    # --- profitandloss ---
    pl_raw = load_profitandloss()
    rows_in = len(pl_raw)
    pl, _ = deduplicate_annual_table(pl_raw, "profitandloss")
    pl, _ = exclude_orphan_rows(pl, companies, "profitandloss")
    audit_rows.append(load_and_track(conn, pl, insert_profitandloss, "profitandloss", rows_in))

    # --- balancesheet ---
    bs_raw = load_balancesheet()
    rows_in = len(bs_raw)
    bs, _ = deduplicate_annual_table(bs_raw, "balancesheet")
    bs, _ = exclude_orphan_rows(bs, companies, "balancesheet")
    audit_rows.append(load_and_track(conn, bs, insert_balancesheet, "balancesheet", rows_in))

    # --- cashflow ---
    cf_raw = load_cashflow()
    rows_in = len(cf_raw)
    cf, _ = deduplicate_annual_table(cf_raw, "cashflow")
    cf, _ = exclude_orphan_rows(cf, companies, "cashflow")
    audit_rows.append(load_and_track(conn, cf, insert_cashflow, "cashflow", rows_in))

    # --- analysis ---
    analysis_raw = load_analysis()
    rows_in = len(analysis_raw)
    analysis, _ = exclude_orphan_rows(analysis_raw, companies, "analysis")
    audit_rows.append(load_and_track(conn, analysis, insert_analysis, "analysis", rows_in))

    # --- documents ---
    documents_raw = load_documents()
    rows_in = len(documents_raw)
    documents, _ = deduplicate_documents(documents_raw)
    documents, _ = exclude_orphan_rows(documents, companies, "documents")
    audit_rows.append(load_and_track(conn, documents, insert_documents, "documents", rows_in))

    # --- prosandcons ---
    prosandcons_raw = load_prosandcons()
    rows_in = len(prosandcons_raw)
    prosandcons, _ = exclude_orphan_rows(prosandcons_raw, companies, "prosandcons")
    audit_rows.append(load_and_track(conn, prosandcons, insert_prosandcons, "prosandcons", rows_in))

    # --- stock_prices ---
    stock_prices = load_stock_prices()
    audit_rows.append(load_and_track(conn, stock_prices, insert_stock_prices, "stock_prices", len(stock_prices)))

    # --- market_cap ---
    market_cap = load_market_cap()
    audit_rows.append(load_and_track(conn, market_cap, insert_market_cap, "market_cap", len(market_cap)))

    # --- financial_ratios ---
    fr_raw = load_financial_ratios()
    rows_in = len(fr_raw)
    financial_ratios, _ = deduplicate_financial_ratios(fr_raw)
    financial_ratios, _ = exclude_orphan_rows(financial_ratios, companies, "financial_ratios")
    audit_rows.append(load_and_track(conn, financial_ratios, insert_financial_ratios, "financial_ratios", rows_in))

    # --- peer_groups ---
    peer_groups = load_peer_groups()
    audit_rows.append(load_and_track(conn, peer_groups, insert_peer_groups, "peer_groups", len(peer_groups)))

    fk_check = conn.execute("PRAGMA foreign_key_check").fetchall()
    conn.close()

    print()
    print("Row counts:")
    for row in audit_rows:
        print(f"  {row['table']}: in={row['rows_in']}, out={row['rows_out']}, rejected={row['rejected']}")

    print()
    print("Foreign key violations:", len(fk_check))

    import pandas as pd
    audit_df = pd.DataFrame(audit_rows)
    audit_df.to_csv("output/load_audit.csv", index=False)
    print()
    print("Saved output/load_audit.csv")