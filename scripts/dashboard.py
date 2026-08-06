import os
from datetime import datetime, timezone

from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "index.html")

CATEGORY_LABELS = {
    "housing": "Housing",
    "transit": "Transit",
    "biking_pedestrian": "Biking & Pedestrian",
}


def _group_by_council(items: list[dict]) -> list[tuple[str, list[dict]]]:
    # Newest-first within each council; items don't carry a reliable meeting
    # date yet, so we rely on list order (new items are appended as found).
    by_council: dict[str, list[dict]] = {}
    for item in items:
        by_council.setdefault(item["council"], []).append(item)
    for group in by_council.values():
        group.reverse()
    return sorted(by_council.items(), key=lambda kv: kv[0])


def render_dashboard(items: list[dict], output_path: str = OUTPUT_PATH) -> None:
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    template = env.get_template("dashboard.html.j2")
    html = template.render(
        grouped=_group_by_council(items),
        total_items=len(items),
        category_labels=CATEGORY_LABELS,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
