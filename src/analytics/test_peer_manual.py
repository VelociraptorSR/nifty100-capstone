"""Manual verification for peer percentile rankings — Sprint 3, Day 18."""

import sqlite3

from src.analytics.peer import compute_peer_percentiles

DB_PATH = "data/nifty100.db"

if __name__ == "__main__":
    from src.analytics.peer import write_peer_percentiles

    conn = sqlite3.connect(DB_PATH)
    percentiles = compute_peer_percentiles(conn)
    write_peer_percentiles(conn, percentiles)

    count = conn.execute("SELECT COUNT(*) FROM peer_percentiles").fetchone()[0]
    print("peer_percentiles rows written:", count)

    conn.close()