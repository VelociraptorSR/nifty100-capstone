"""Manual verification for pros/cons generator — Sprint 5, Day 30."""

import sqlite3
import pandas as pd

from src.nlp.pros_cons_generator import (
    get_company_history,
    pro_rule_1_high_roe_sustained,
    pro_rule_2_fcf_positive_5yr,
    pro_rule_3_debt_free,
    pro_rule_4_revenue_cagr_15,
    pro_rule_5_high_opm,
)

DB_PATH = "data/nifty100.db"

if __name__ == "__main__":
    from src.nlp.pros_cons_generator import generate_all_pros_cons, save_pros_cons

    conn = sqlite3.connect(DB_PATH)
    result_df, missing_pro, missing_con = generate_all_pros_cons(conn)
    conn.close()

    print("Total signals generated:", len(result_df))
    print("Companies missing at least 1 pro:", len(missing_pro))
    print("Companies missing at least 1 con:", len(missing_con))

    path = save_pros_cons(result_df)
    print("Saved:", path)