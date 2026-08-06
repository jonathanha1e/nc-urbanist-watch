import re
from datetime import datetime

import pdfplumber

MONTH_NAME_DATE_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b",
    re.IGNORECASE,
)
NUMERIC_DATE_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")


def extract_pdf_text(path: str) -> str:
    """Extracts all text from a PDF, page by page, joined with blank lines."""
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n\n".join(pages)


def extract_meeting_date(text: str) -> str | None:
    """Finds the meeting date in agenda text, e.g. "Saturday, March 15, 2025"
    (the usual placement, near the top, right after the meeting title/venue).
    Returns an ISO date string (first match found), or None if no date-like
    text is present.
    """
    match = MONTH_NAME_DATE_RE.search(text)
    if match:
        month_name, day, year = match.groups()
        try:
            return datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y").date().isoformat()
        except ValueError:
            pass

    match = NUMERIC_DATE_RE.search(text)
    if match:
        month, day, year = match.groups()
        try:
            return datetime.strptime(f"{month}/{day}/{year}", "%m/%d/%Y").date().isoformat()
        except ValueError:
            pass

    return None
