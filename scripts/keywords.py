"""Keyword rules for flagging urbanist advocacy opportunities in NC agenda text.

The actual terms live in keywords.json, not here -- to add/remove/edit terms,
just edit that file's arrays (one string per term or phrase, case doesn't
matter). No code changes needed. Categories are fixed to "housing",
"transit", and "mobility" since the dashboard filters by those three.

Matching is deliberately simple (case-insensitive word/phrase search) rather
than NLP -- it will over-flag routine items (e.g. a Metro update with no real
decision) and under-flag agenda items that use unusual phrasing. Treat it as a
triage filter: read the flagged items, don't trust the category blindly.
"""
import json
import os
import re

CATEGORY_LABELS = {
    "housing": "Housing",
    "transit": "Transit",
    "mobility": "Mobility",
}

_KEYWORDS_PATH = os.path.join(os.path.dirname(__file__), "keywords.json")

# Words that suggest the item is an actual decision point (vs. an FYI report),
# useful for sorting flagged items by how actionable they are.
ACTIONABLE_TERMS = [
    "public hearing", "public comment", "motion to", "recommend", "vote",
    "approve", "oppose", "support letter", "community impact statement",
    "cis", "board action",
]


def _load_categories() -> dict[str, list[str]]:
    with open(_KEYWORDS_PATH, encoding="utf-8") as f:
        return json.load(f)


def _word_bounded(term: str) -> re.Pattern:
    return re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)


CATEGORIES = _load_categories()
_CATEGORY_PATTERNS = {
    category: [_word_bounded(term) for term in terms]
    for category, terms in CATEGORIES.items()
}
_ACTIONABLE_PATTERN = re.compile(
    "|".join(rf"\b{re.escape(t)}\b" for t in ACTIONABLE_TERMS), re.IGNORECASE
)


def scan_text(text: str, context_chars: int = 120) -> list[dict]:
    """Finds keyword hits in agenda text.

    Returns one entry per matched term occurrence, each with the category,
    the matched term, a surrounding text snippet, and whether the snippet
    also contains actionable-item language.
    """
    hits = []
    for category, patterns in _CATEGORY_PATTERNS.items():
        for pattern in patterns:
            for match in pattern.finditer(text):
                start = max(0, match.start() - context_chars)
                end = min(len(text), match.end() + context_chars)
                snippet = " ".join(text[start:end].split())
                hits.append({
                    "category": category,
                    "term": match.group(0),
                    "snippet": snippet,
                    "actionable": bool(_ACTIONABLE_PATTERN.search(snippet)),
                })
    return hits
