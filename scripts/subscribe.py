"""One-time (or re-run-safe) script: subscribes one email address to all 99
LA Neighborhood Council agenda lists via the city's ENS form.

The ENS form (https://ens2.lacity.org/index2_ctn_lacitynewnc.cfm) renders 99
same-named radio inputs, one per council -- so despite looking like a
multi-select checkbox list, the browser only ever lets a person submit one at
a time. We replicate that: one POST per council, same name/email each time.

Defaults to DRY_RUN=true, which prints every request instead of sending it.
Re-running with DRY_RUN=false is safe to repeat -- ENS's "su" (subscribe)
action is idempotent per council per address, it just re-confirms.
"""
import json
import os
import subprocess
import time

from dotenv import load_dotenv

ENS_URL = "https://ens2.lacity.org/index2_ctn_lacitynewnc.cfm?fuseaction=su"
COUNCILS_PATH = os.path.join(os.path.dirname(__file__), "councils.json")
USER_AGENT = "NCUrbanistWatch/1.0 (personal use; contact: jonathan.hale@rocketmail.com)"


def load_councils() -> dict[str, str]:
    with open(COUNCILS_PATH, encoding="utf-8") as f:
        return json.load(f)


def subscribe_one(name: str, email_addr: str, mlist_id: str, council_name: str, dry_run: bool) -> None:
    payload = {
        "subname": name,
        "subemail": email_addr,
        "mlist": f"{mlist_id}:{council_name}",
    }
    if dry_run:
        print(f"[DRY RUN] would POST {ENS_URL} with {payload}")
        return

    # requests/urllib3's TLS ClientHello gets reset by this server (an old IIS
    # box, possibly behind a WAF that fingerprints non-browser-like TLS
    # handshakes) even though the request itself is fine -- confirmed curl
    # succeeds against the identical endpoint/payload. Shelling out to curl
    # sidesteps that instead of fighting Python's TLS stack.
    args = ["curl", "-sS", "-A", USER_AGENT, "-X", "POST", ENS_URL]
    for key, value in payload.items():
        args += ["--data-urlencode", f"{key}={value}"]

    result = subprocess.run(args, capture_output=True, text=True, timeout=20)
    ok = "Confirmation Notice" in result.stdout
    print(f"{council_name}: {'OK' if ok else 'UNEXPECTED RESPONSE'} (curl exit {result.returncode})")
    if not ok:
        print(f"  response snippet: {result.stdout[:300]!r}")


def main() -> None:
    load_dotenv()
    dry_run = os.environ.get("DRY_RUN", "true").lower() == "true"
    name = os.environ["ENS_SUBSCRIBER_NAME"]
    email_addr = os.environ["ENS_SUBSCRIBER_EMAIL"]

    councils = load_councils()
    print(f"Subscribing {email_addr} to {len(councils)} councils. DRY_RUN={dry_run}")

    for mlist_id, council_name in councils.items():
        subscribe_one(name, email_addr, mlist_id, council_name, dry_run)
        if not dry_run:
            time.sleep(0.5)  # avoid hammering a small city government server

    print("Done.")


if __name__ == "__main__":
    main()
