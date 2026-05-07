"""09 — Watchlist: check fanedits by slug for new ratings.

Shows: get_detail_by_slug(), comparing rating fields across runs,
persisting state to JSON for periodic cron/scheduler use.

Run periodically; state is stored in watchlist_state.json.
"""
import json
import os
from datetime import datetime

from pyfanedit import FaneditClient

STATE_FILE = "watchlist_state.json"

WATCHLIST = [
    "star-wars-begins",
    "batman-returns-the-eyepainter-fanedit",
    "sin-city-roark-dynasty-cut",
]

client = FaneditClient()

# Load previous state
state: dict = {}
if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        state = json.load(f)

now = datetime.utcnow().isoformat()
changed: list[str] = []

for slug in WATCHLIST:
    print(f"Checking: {slug}")
    try:
        detail = client.get_detail_by_slug(slug)
    except Exception as exc:
        print(f"  ERROR: {exc}")
        continue

    prev = state.get(slug, {})
    curr = {
        "title": detail.title,
        "editor_rating": detail.editor_rating,
        "user_rating": detail.user_rating,
        "user_rating_count": detail.user_rating_count,
        "checked_at": now,
    }

    if prev.get("editor_rating") != curr["editor_rating"]:
        print(f"  editor_rating changed: {prev.get('editor_rating')} → {curr['editor_rating']}")
        changed.append(slug)
    elif prev.get("user_rating") != curr["user_rating"]:
        print(f"  user_rating changed: {prev.get('user_rating')} → {curr['user_rating']}")
        changed.append(slug)
    else:
        print(f"  no change  (editor={curr['editor_rating']}  user={curr['user_rating']})")

    state[slug] = curr

with open(STATE_FILE, "w") as f:
    json.dump(state, f, indent=2)

print(f"\nChecked {len(WATCHLIST)} slugs.  Changed: {changed or 'none'}")
print(f"State saved to {STATE_FILE}")
