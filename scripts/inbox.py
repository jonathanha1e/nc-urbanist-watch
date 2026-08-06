"""Reads ENS agenda-notification emails from the dedicated IMAP inbox.

ENS notifications aren't a documented format -- this handles the two shapes
such notifications commonly take: a PDF file attached directly, or a link to
one (matching the ens.lacity.org/ensnc/<council>/<file>.pdf pattern found by
hand). If real notification emails turn out to look different once they start
arriving, `_extract_pdf_links` / attachment handling are the place to adjust.
"""
import email
import imaplib
import os
import re
from email.message import Message

PDF_LINK_RE = re.compile(r"https?://[^\s\"'<>]+\.pdf", re.IGNORECASE)


def connect() -> imaplib.IMAP4_SSL:
    host = os.environ.get("IMAP_HOST", "imap.gmail.com")
    port = int(os.environ.get("IMAP_PORT", "993"))
    username = os.environ["IMAP_USERNAME"]
    password = os.environ["IMAP_APP_PASSWORD"]

    conn = imaplib.IMAP4_SSL(host, port)
    conn.login(username, password)
    return conn


def _extract_pdf_links(text: str) -> list[str]:
    return list(dict.fromkeys(PDF_LINK_RE.findall(text)))


def _walk_parts(msg: Message):
    if msg.is_multipart():
        for part in msg.walk():
            yield part
    else:
        yield msg


def parse_notification(msg: Message) -> dict:
    """Extracts subject, sender, PDF links, and any PDF attachments (as bytes) from one email."""
    subject = msg.get("Subject", "")
    sender = msg.get("From", "")
    links: list[str] = []
    attachments: list[tuple[str, bytes]] = []

    for part in _walk_parts(msg):
        content_type = part.get_content_type()
        filename = part.get_filename() or ""

        if filename.lower().endswith(".pdf"):
            payload = part.get_payload(decode=True)
            if payload:
                attachments.append((filename, payload))
        elif content_type in ("text/plain", "text/html"):
            payload = part.get_payload(decode=True)
            if payload:
                charset = part.get_content_charset() or "utf-8"
                links.extend(_extract_pdf_links(payload.decode(charset, errors="replace")))

    return {
        "subject": subject,
        "sender": sender,
        "pdf_links": list(dict.fromkeys(links)),
        "pdf_attachments": attachments,
    }


def fetch_new_notifications(conn: imaplib.IMAP4_SSL, seen_uids: set[str]) -> list[dict]:
    """Fetches ENS notification emails not already in `seen_uids`, returning parsed results with their UIDs."""
    sender_filter = os.environ.get("ENS_SENDER_FILTER", "lacity.org")
    conn.select("INBOX")

    status, data = conn.uid("search", None, "ALL")
    if status != "OK":
        return []

    results = []
    for uid in data[0].split():
        uid_str = uid.decode()
        if uid_str in seen_uids:
            continue

        status, msg_data = conn.uid("fetch", uid, "(RFC822)")
        if status != "OK" or not msg_data or not msg_data[0]:
            continue

        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        if sender_filter.lower() not in msg.get("From", "").lower():
            continue

        parsed = parse_notification(msg)
        parsed["uid"] = uid_str
        results.append(parsed)

    return results
