"""Initialise the SQLite database from db/schema.sql.

Run this script directly to (re)create data/nifty100.db with all tables
defined in the schema file.
"""
import pandas as pd
import sqlite3

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


if __name__ == "__main__":
    from src.etl.loader import (
        load_companies, load_sectors, load_profitandloss, load_balancesheet,
        load_cashflow, load_analysis, load_documents, load_prosandcons,
        load_stock_prices, load_market_cap, load_financial_ratios, load_peer_groups,
    )
    from src.etl.validator import deduplicate_annual_table, deduplicate_documents, deduplicate_financial_ratios, exclude_orphan_rows
    tables = init_db()
    print("Tables created:", len(tables))

    conn = get_connection()

    companies = load_companies()
    sectors = load_sectors()
    pl = load_profitandloss()
    bs = load_balancesheet()
    cf = load_cashflow()
    analysis = load_analysis()
    documents = load_documents()
    prosandcons = load_prosandcons()
    stock_prices = load_stock_prices()
    market_cap = load_market_cap()
    financial_ratios = load_financial_ratios()
    peer_groups = load_peer_groups()

    pl, _ = deduplicate_annual_table(pl, "profitandloss")
    pl, _ = exclude_orphan_rows(pl, companies, "profitandloss")

    bs, _ = deduplicate_annual_table(bs, "balancesheet")
    bs, _ = exclude_orphan_rows(bs, companies, "balancesheet")

    cf, _ = deduplicate_annual_table(cf, "cashflow")
    cf, _ = exclude_orphan_rows(cf, companies, "cashflow")
    
    analysis, _ = exclude_orphan_rows(analysis, companies, "analysis")
    documents, _ = deduplicate_documents(documents)
    documents, _ = exclude_orphan_rows(documents, companies, "documents")
    prosandcons, _ = exclude_orphan_rows(prosandcons, companies, "prosandcons")
    financial_ratios, _ = deduplicate_financial_ratios(financial_ratios)
    financial_ratios, _ = exclude_orphan_rows(financial_ratios, companies, "financial_ratios")

    insert_companies(conn, companies)
    insert_sectors(conn, sectors)
    insert_profitandloss(conn, pl)
    insert_balancesheet(conn, bs)
    insert_cashflow(conn, cf)
    insert_analysis(conn, analysis)
    insert_documents(conn, documents)
    insert_prosandcons(conn, prosandcons)
    insert_stock_prices(conn, stock_prices)
    insert_market_cap(conn, market_cap)
    insert_financial_ratios(conn, financial_ratios)
    insert_peer_groups(conn, peer_groups)
    conn.commit()

    print()
    print("Row counts:")
    for table_name in ["companies", "sectors", "profitandloss", "balancesheet",
                        "cashflow", "analysis", "documents", "prosandcons",
                        "stock_prices", "market_cap", "financial_ratios", "peer_groups"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"  {table_name}: {count}")

    fk_check = conn.execute("PRAGMA foreign_key_check").fetchall()
    print()
    print("Foreign key violations:", len(fk_check))

    conn.close()