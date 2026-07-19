"""Run and display results from notebooks/exploratory_queries.sql — Day 07."""

import re
import sqlite3

DB_PATH = "data/nifty100.db"
SQL_PATH = "notebooks/exploratory_queries.sql"


def run_all_queries():
    conn = sqlite3.connect(DB_PATH)

    with open(SQL_PATH, "r") as f:
        script = f.read()

    raw_statements = [s.strip() for s in script.split(";") if s.strip()]

    query_num = 0
    for stmt in raw_statements:
        clean_stmt = re.sub(r"--.*", "", stmt).strip()
        if not clean_stmt:
            continue
        query_num += 1
        try:
            cursor = conn.execute(clean_stmt)
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]
            print(f"--- Query {query_num}: OK, {len(rows)} rows ---")
            print(col_names)
            for row in rows[:5]:
                print(row)
            print()
        except Exception as e:
            print(f"--- Query {query_num}: ERROR - {e} ---")
            print()

    conn.close()


if __name__ == "__main__":
    run_all_queries()