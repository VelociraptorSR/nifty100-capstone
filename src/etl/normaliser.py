"""Normalisation functions for the Nifty 100 ETL pipeline."""

import re


def normalize_ticker(raw_ticker):
    """Clean a company ticker: strip whitespace, uppercase, validate length.

    Returns the cleaned ticker string, or None if invalid (e.g. missing,
    or outside the 2-12 character range expected for NSE tickers).
    """
    if raw_ticker is None:
        return None

    ticker = str(raw_ticker).strip().upper()

    if len(ticker) < 2 or len(ticker) > 12:
        return None

    return ticker


_MONTH_MAP = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
    "january": "01", "february": "02", "march": "03", "april": "04",
    "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}


def normalize_year(raw_year):
    """Convert a messy financial-year label into standard 'YYYY-MM' format.

    Handles formats like 'Mar-23', 'Mar 23', 'March-2023', '2023', 'FY23',
    'Dec-22', and already-normalised '2023-03'. Returns 'PARSE_ERROR' string
    if the input cannot be understood (per DQ-07 in the project spec).
    """
    if raw_year is None:
        return "PARSE_ERROR"

    text = str(raw_year).strip()
    
    # TTM = Trailing Twelve Months — not a fixed fiscal year, handle separately
    if text.upper() == "TTM":
        return "TTM"

    # Already normalised: e.g. "2023-03"
    if re.match(r"^\d{4}-\d{2}$", text):
        return text

    # Plain 4-digit year: e.g. "2023" -> assume March FY close
    if re.match(r"^\d{4}$", text):
        return f"{text}-03"

    # FY prefix: e.g. "FY23" -> "2023-03"
    fy_match = re.match(r"^FY(\d{2})$", text, re.IGNORECASE)
    if fy_match:
        yy = fy_match.group(1)
        return f"20{yy}-03"

    # Month-Year formats: "Mar-23", "Mar 23", "March-2023", "Dec-22"
    my_match = re.match(
        r"^([A-Za-z]+)[\s\-]+(\d{2,4})$", text
    )
    if my_match:
        month_name = my_match.group(1).lower()
        year_part = my_match.group(2)

        if month_name not in _MONTH_MAP:
            return "PARSE_ERROR"

        month_num = _MONTH_MAP[month_name]

        if len(year_part) == 2:
            year_full = f"20{year_part}"
        else:
            year_full = year_part

        return f"{year_full}-{month_num}"

    return "PARSE_ERROR"