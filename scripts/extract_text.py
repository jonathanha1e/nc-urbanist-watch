import re
from datetime import datetime

import pdfplumber

MONTH_NAME_DATE_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b",
    re.IGNORECASE,
)
# Covers both "11/20/2025" and "11.20.2025" -- both show up in the wild.
NUMERIC_DATE_RE = re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b")

# The meeting date reliably appears in the first few lines (title/venue/date
# block), before any agenda items that might themselves mention unrelated
# dates (deadlines, past meeting references, etc). Searching only this
# header window avoids picking up one of those instead.
HEADER_WINDOW_CHARS = 800


def extract_pdf_text(path: str) -> str:
    """Extracts all text from a PDF, page by page, joined with blank lines."""
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n\n".join(pages)


def _earliest_match(text: str):
    candidates = [m for m in (MONTH_NAME_DATE_RE.search(text), NUMERIC_DATE_RE.search(text)) if m]
    return min(candidates, key=lambda m: m.start()) if candidates else None


def _parse_match(match: re.Match) -> str | None:
    groups = match.groups()
    try:
        if match.re is MONTH_NAME_DATE_RE:
            month_name, day, year = groups
            return datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y").date().isoformat()
        month, day, year = groups
        return datetime.strptime(f"{month}/{day}/{year}", "%m/%d/%Y").date().isoformat()
    except ValueError:
        return None


def extract_meeting_date(text: str) -> str | None:
    """Finds the meeting date in agenda text, e.g. "Saturday, March 15, 2025"
    or "11.20.2025" (the usual placement, near the top, right after the
    meeting title/venue). Returns an ISO date string, preferring whichever
    date-like text appears earliest, or None if nothing is found.
    """
    match = _earliest_match(text[:HEADER_WINDOW_CHARS])
    if match is None:
        match = _earliest_match(text)  # fall back to the whole document
    return _parse_match(match) if match else None
