import json
import os
from datetime import datetime, timezone

from jinja2 import Environment, FileSystemLoader

from keywords import CATEGORY_LABELS

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "index.html")


def _embeddable_json(data) -> str:
    # Prevents a stray "</script>" inside agenda text/snippets from closing
    # the surrounding <script> tag early.
    return json.dumps(data).replace("</", "<\\/")


def render_dashboard(items: list[dict], output_path: str = OUTPUT_PATH) -> None:
    councils = sorted({item["council"] for item in items})

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    template = env.get_template("dashboard.html.j2")
    html = template.render(
        items_json=_embeddable_json(items),
        councils_json=_embeddable_json(councils),
        category_labels_json=_embeddable_json(CATEGORY_LABELS),
        category_labels=CATEGORY_LABELS,
        total_items=len(items),
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
