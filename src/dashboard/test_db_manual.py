"""Manual verification for src/dashboard/utils/db.py — Sprint 4, Day 22.

Streamlit's @st.cache_data decorator requires a Streamlit runtime context
to work fully, but the underlying SQL logic can still be exercised directly
here to catch basic errors before wiring it into actual pages.
"""

from src.dashboard.utils.db import (
    get_companies, get_ratios, get_pl, get_bs, get_cf,
    get_sectors, get_peers, get_valuation,
)

if __name__ == "__main__":
    companies = get_companies()
    print("get_companies():", companies.shape)
    print(companies.head(3))
    print()

    ratios = get_ratios("TCS")
    print("get_ratios('TCS'):", ratios.shape)
    print()

    ratios_2024 = get_ratios("TCS", year="2024-03")
    print("get_ratios('TCS', '2024-03'):", ratios_2024.shape)
    print()

    pl = get_pl("TCS")
    print("get_pl('TCS'):", pl.shape)

    bs = get_bs("TCS")
    print("get_bs('TCS'):", bs.shape)

    cf = get_cf("TCS")
    print("get_cf('TCS'):", cf.shape)

    sectors = get_sectors()
    print("get_sectors():", sectors.shape)

    peers = get_peers("IT Services")
    print("get_peers('IT Services'):", peers.shape)

    valuation = get_valuation("TCS")
    print("get_valuation('TCS'):", valuation.shape)