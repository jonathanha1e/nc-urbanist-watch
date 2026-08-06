import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SEEN_PATH = os.path.join(DATA_DIR, "seen_uids.json")
ITEMS_PATH = os.path.join(DATA_DIR, "items.json")


def load_seen_uids() -> set[str]:
    if not os.path.exists(SEEN_PATH):
        return set()
    with open(SEEN_PATH, encoding="utf-8") as f:
        return set(json.load(f))


def save_seen_uids(uids: set[str]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(uids), f, indent=2)


def load_items() -> list[dict]:
    if not os.path.exists(ITEMS_PATH):
        return []
    with open(ITEMS_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_items(items: list[dict]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ITEMS_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)
