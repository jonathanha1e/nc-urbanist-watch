import json
import os

_PATH = os.path.join(os.path.dirname(__file__), "councils.json")

with open(_PATH, encoding="utf-8") as _f:
    COUNCILS: dict[str, str] = json.load(_f)

_NAMES_BY_LENGTH = sorted(COUNCILS.values(), key=len, reverse=True)


def match_council_name(text: str) -> str:
    """Finds which council an ENS notification is for by matching its name in
    the email subject. Longest names are checked first so e.g. "Granada Hills
    South NC" doesn't get mis-matched to "Granada Hills North NC" fragments.
    Falls back to the raw subject if no known council name is found -- ENS
    subject formatting for real notifications hasn't been observed yet.
    """
    lowered = text.lower()
    for name in _NAMES_BY_LENGTH:
        if name.lower() in lowered:
            return name
    return text.strip() or "Unknown Council"
