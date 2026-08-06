"""Keyword rules for flagging urbanist advocacy opportunities in NC agenda text.

Matching is deliberately simple (case-insensitive substring/phrase search) rather
than NLP -- it will over-flag routine items (e.g. a Metro update with no real
decision) and under-flag agenda items that use unusual phrasing. Treat it as a
triage filter: read the flagged items, don't trust the category blindly.
"""
import re

CATEGORIES: dict[str, list[str]] = {
    "housing": [
        "affordable housing", "accessory dwelling unit", "adu", "upzon",
        "rezon", "zone change", "zoning ordinance", "density bonus",
        "housing element", "general plan amendment", "specific plan",
        "mixed-use", "mixed use", "multifamily", "multi-family",
        "supportive housing", "transit oriented communities", "toc project",
        "sb 9", "sb 35", "sb9", "sb35", "builder's remedy",
        "conditional use permit", "variance", "parking minimum",
        "parking requirement", "new construction", "residential project",
        "apartment complex", "condominium project", "duplex", "fourplex",
        "subdivision map", "spot zoning", "environmental impact report",
        "by-right", "rent stabilization ordinance", "rso", "just cause eviction",
        "single family zoning", "r1 zone", "granny flat",
    ],
    "transit": [
        "metro board", "metro rail", "metro rapid", "bus rapid transit", "brt",
        "bus lane", "dedicated bus lane", "light rail", "subway extension",
        "transit priority", "first/last mile", "first mile last mile",
        "dash route", "ladot transit", "microtransit", "metro line",
        "transit stop relocation", "bus stop relocation", "park and ride",
        "metro fare", "expo line", "purple line", "d line", "k line", "g line",
        "regional connector", "transit oriented",
    ],
    "biking_pedestrian": [
        "bike lane", "protected bike lane", "bikeway", "bike share",
        "metro bike", "road diet", "complete streets", "vision zero",
        "pedestrian safety", "crosswalk", "curb extension", "bulb-out",
        "bulbout", "traffic calming", "sidewalk repair", "sidewalk widening",
        "mobility plan", "slow streets", "ciclovia", "scramble crosswalk",
        "lane reduction", "measure hla", "hla ordinance", "mobility plan 2035",
        "protected intersection", "raised crosswalk", "road safety",
    ],
}

# Words that suggest the item is an actual decision point (vs. an FYI report),
# useful for sorting flagged items by how actionable they are.
ACTIONABLE_TERMS = [
    "public hearing", "public comment", "motion to", "recommend", "vote",
    "approve", "oppose", "support letter", "community impact statement",
    "cis", "board action",
]

def _word_bounded(term: str) -> re.Pattern:
    return re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)


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
