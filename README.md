# NC Urbanist Watch

A personal tool that watches Los Angeles's 99 Neighborhood Council agendas for
items relevant to housing, transit, and mobility (bike/pedestrian)
infrastructure advocacy, and publishes a filterable dashboard of what it finds.

**Live dashboard: https://jonathanha1e.github.io/nc-urbanist-watch/**

Runs automatically every 6 hours via GitHub Actions (see
`.github/workflows/watch.yml`), committing updated state and dashboard back
to this repo, which GitHub Pages serves from `docs/`.

## Why it works the way it does

LA has no single reliable, current, machine-readable feed of NC agendas as of
this writing (Aug 2026):

- The new lacity.gov "Neighborhood Council Meetings" calendar widget loads
  but returns zero events (verified directly against its API).
- The old ENS web portal (`ens.lacity.org`) frontend is gone (403) -- though
  raw PDF files hosted there are still directly reachable if you already know
  the URL.
- EmpowerLA (`neighborhoodempowerment.lacity.gov` / `empowerla.org`) is
  currently returning server errors (verified via two independent fetches).

The one thing that *is* alive: the ENS **email subscription** system at
`ens2.lacity.org` -- an old but functional ColdFusion form that emails a PDF
link every time a council posts a new agenda. So this tool subscribes a
dedicated inbox to all 99 councils and watches that inbox instead of trying
to scrape a website.

## How it works

1. `scripts/subscribe.py` subscribes one email address to all 99 councils via
   the ENS form (`scripts/councils.json` has the council name -> ENS list ID
   mapping, scraped by hand from the live form).
2. `scripts/inbox.py` connects to that inbox over IMAP and finds new ENS
   notification emails.
3. `scripts/main.py` downloads/extracts each notification's agenda PDF
   (`scripts/extract_text.py`, which also tries to pull out the meeting date),
   scans the text for housing/transit/mobility keywords (`scripts/keywords.py`
   + `scripts/keywords.json`), and records any hits.
4. `scripts/state.py` tracks which emails have already been processed
   (`data/seen_uids.json`) and accumulates flagged items (`data/items.json`)
   across runs.
5. `scripts/dashboard.py` renders `docs/index.html` from the accumulated
   items: a reverse-chronological feed grouped by meeting date, filterable in
   the browser by topic (housing/transit/mobility) and by council.

### Editing the keyword list

All the terms live in `scripts/keywords.json`, grouped under `"housing"`,
`"transit"`, and `"mobility"` -- to add or remove a term, just edit that
file's arrays (no code changes, no restart needed beyond the next run). Terms
are matched as whole words/phrases, case-insensitively.

Keyword matching is a **triage filter, not a judgment call** -- it flags
agenda items containing terms like "zone change," "bike lane," or "bus rapid
transit" along with a snippet of surrounding text, but it will miss items
using unusual phrasing and can over-flag routine informational items. Read
the flagged items yourself; don't treat a flag as confirmation something is
actually up for a vote.

## Setup

1. Create a fresh Python virtual environment and install dependencies:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Create a dedicated inbox for this (don't use your personal email --
   99 subscriptions is a lot of city mail). Gmail is recommended since it has
   well-documented IMAP + app password support:
   - Create the account.
   - Turn on 2-Step Verification (Google Account -> Security).
   - Generate an App Password for "Mail" (Google Account -> Security ->
     App Passwords).
3. Copy `.env.example` to `.env` and fill in `IMAP_USERNAME`,
   `IMAP_APP_PASSWORD`, `ENS_SUBSCRIBER_NAME`, `ENS_SUBSCRIBER_EMAIL`.
4. Run the subscription step in dry-run first to see exactly what it would
   send, with no real requests made:
   ```
   cd scripts && python subscribe.py
   ```
   Then set `DRY_RUN=false` in `.env` and re-run to actually subscribe.
5. Run the watcher:
   ```
   cd scripts && python main.py
   ```
   Open `docs/index.html` in a browser to see results. Re-running `main.py`
   only processes emails it hasn't seen before.

## Automation (GitHub Actions + Pages)

This repo is wired to run unattended:

- `IMAP_USERNAME` and `IMAP_APP_PASSWORD` are stored as GitHub Actions
  secrets (Settings -> Secrets and variables -> Actions), not committed.
- `.github/workflows/watch.yml` runs `main.py` every 6 hours, then commits
  `data/seen_uids.json`, `data/items.json`, and `docs/index.html` if they
  changed.
- GitHub Pages is configured to serve `docs/` from the `master` branch, so the
  dashboard is live at the URL above without any separate deploy step.
- Trigger a run manually anytime from the Actions tab ("NC Urbanist Watch" ->
  Run workflow), or with `gh workflow run watch.yml -f dry_run=false`.

## Known limitations / things to revisit

- `scripts/councils.py`'s `match_council_name` guesses which council an
  email is for by matching council names against the email subject line.
  Real ENS notification subject/body formatting hasn't been observed yet
  (the form only sends when a council actually posts something new) --
  once real notifications start arriving, check that this still works and
  adjust `inbox.py` / `councils.py` if the format differs from what's
  assumed.
- If LA's official systems (lacity.gov calendar, EmpowerLA) come back online
  later, they'd be a more complete and more real-time source than
  email notifications and worth revisiting.
