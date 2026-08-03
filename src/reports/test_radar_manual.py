"""Manual verification for radar chart generation — Sprint 3, Day 19."""

import os
import sqlite3

from src.reports.radar_charts import get_normalized_axis_values, draw_radar_chart, AXES, OUTPUT_DIR
from src.screener.engine import build_screener_dataset

DB_PATH = "data/nifty100.db"

if __name__ == "__main__":
    from src.reports.radar_charts import generate_all_radar_charts

    conn = sqlite3.connect(DB_PATH)
    generated = generate_all_radar_charts(conn)
    conn.close()

    print("Total charts generated:", len(generated))

    import os
    files = os.listdir(OUTPUT_DIR)
    print("Files in output dir:", len(files))

    print("TCS_radar.png exists:", "TCS_radar.png" in files)
    print("Sample filenames:", files[:5])