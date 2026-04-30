"""
User story: I have a watchlist of fanedits saved by their slug or URL.
Check which ones now have trusted reviewer ratings they didn't have before,
and print a digest.

Shows: get_detail() by slug, comparing ratings, building a simple
change-detection loop (run it periodically from cron or a scheduler).

Persist state in a local JSON file between runs.
"""
import json
import os
from datetime import datetime

from pyfanedit import FaneditClient

STATE_FILE = "watchlist_state.json"

# Your personal watchlist — add/remove slugs freely
WATCHLIST = [
    "star-wars-begins",
    "batman-returns-the-eyepainter-fanedit",
    "sin-city-roark-dynasty-cut",
    "dont-say-a-word-the-unfair-cut",
    "star-wars-episode-iii-labyrinth-of-evil",
]

client = FaneditClient()

# Load previous state
previous: dict = {}
if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        previous = json.load(f)

current: dict = {}
changes: list = []

print(f"Checking {len(WATCHLIST)} watchlisted fanedits...\n")

for slug in WATCHLIST:
    detail = client.get_detail(slug)
    state = {
        "title": detail.title,
        "editor_rating": detail.editor_rating,
        "user_rating": detail.user_rating,
        "user_rating_count": detail.user_rating_count,
        "editor_reviews": len(detail.editor_reviews),
        "user_reviews": len(detail.user_reviews),
        "checked_at": datetime.now().isoformat(),
    }
    current[slug] = state

    prev = previous.get(slug, {})
    diffs = []
    if prev.get("editor_rating") != state["editor_rating"]:
        diffs.append(f"editor rating: {prev.get('editor_rating')} → {state['editor_rating']}")
    if prev.get("user_rating_count") != state["user_rating_count"]:
        diffs.append(
            f"user reviews: {prev.get('user_rating_count', 0)} → {state['user_rating_count']}"
        )
    if prev.get("editor_reviews") != state["editor_reviews"]:
        diffs.append(
            f"editor reviews: {prev.get('editor_reviews', 0)} → {state['editor_reviews']}"
        )

    if diffs:
        changes.append((detail.title, detail.url, diffs))
        print(f"  CHANGED  {detail.title}")
        for d in diffs:
            print(f"           {d}")
    else:
        er = f"{state['editor_rating']:.1f}" if state["editor_rating"] else "  - "
        ur = f"{state['user_rating']:.1f}" if state["user_rating"] else "  - "
        print(f"  no change  {detail.title}  (editor={er} user={ur})")

# Persist new state
with open(STATE_FILE, "w") as f:
    json.dump(current, f, indent=2)

print(f"\n{len(changes)} change(s) detected. State saved to {STATE_FILE}.")
if changes:
    print("\nDigest:")
    for title, url, diffs in changes:
        print(f"  {title}")
        print(f"  {url}")
        for d in diffs:
            print(f"    • {d}")
