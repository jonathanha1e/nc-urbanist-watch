"""Orchestrates one run: check inbox for new ENS notifications, download and
scan any agenda PDFs, accumulate flagged items, regenerate the dashboard.
"""
import json
import os
import tempfile

import requests
from dotenv import load_dotenv

import inbox
import state
from councils import match_council_name
from dashboard import render_dashboard
from extract_text import extract_meeting_date, extract_pdf_text
from keywords import scan_text

session = requests.Session()
session.headers.update({
    "User-Agent": "NCUrbanistWatch/1.0 (personal use; contact: jonathan.hale@rocketmail.com)"
})


def _download_pdf(url: str) -> bytes:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return response.content


def _read_pdf_text(pdf_bytes: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        tmp.flush()
        return extract_pdf_text(tmp.name)


def process_notification(note: dict) -> list[dict]:
    """Turns one parsed ENS email into zero or more flagged-item records."""
    council = match_council_name(note["subject"])
    new_items = []

    sources: list[tuple[str, bytes]] = list(note["pdf_attachments"])
    for link in note["pdf_links"]:
        try:
            sources.append((link, _download_pdf(link)))
        except requests.RequestException as e:
            print(f"  failed to download {link}: {e}")

    for source_name, pdf_bytes in sources:
        text = _read_pdf_text(pdf_bytes)
        hits = scan_text(text)
        if not hits:
            continue
        new_items.append({
            "council": council,
            "subject": note["subject"],
            "source": source_name,
            "date": extract_meeting_date(text) or note.get("received_at"),
            "hits": hits,
        })

    return new_items


def main() -> None:
    load_dotenv()

    seen_uids = state.load_seen_uids()
    items = state.load_items()

    conn = inbox.connect()
    try:
        notifications = inbox.fetch_new_notifications(conn, seen_uids)
    finally:
        conn.logout()

    print(f"{len(notifications)} new ENS notification email(s).")

    for note in notifications:
        print(f"Processing: {note['subject']}")
        items.extend(process_notification(note))
        seen_uids.add(note["uid"])

    state.save_seen_uids(seen_uids)
    state.save_items(items)
    render_dashboard(items)
    print(f"Dashboard updated. {len(items)} total flagged items.")


if __name__ == "__main__":
    main()
