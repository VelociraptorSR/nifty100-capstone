"""Manual verification for the analysis text parser — Sprint 5, Day 29."""

from src.nlp.parser import parse_growth_text

if __name__ == "__main__":
    import sqlite3
    from src.nlp.parser import parse_all_analysis_text, cross_validate_cagr

    conn = sqlite3.connect("data/nifty100.db")
    parsed, failures = parse_all_analysis_text(conn)
    merged, flagged = cross_validate_cagr(conn, parsed)
    conn.close()

    print("Total comparisons:", len(merged))
    print(merged[["company_id", "value_pct", "revenue_cagr_5yr", "divergence"]])
    print()
    print("Flagged for manual review (divergence > 5pp):", len(flagged))
    print(flagged[["company_id", "value_pct", "revenue_cagr_5yr", "divergence"]])