"""
User story: I only want to watch the best of the best — Fanedit of the Month
winners. List them all with ratings and genre breakdown.

Shows: get_award_winners(), iter pagination, genre analytics.
"""
from collections import Counter

from pyfanedit import FaneditClient

client = FaneditClient()

print("All Fanedit of the Month award winners\n")

winners = list(client.iter_by_tag("award", "fanedit-of-the-month"))
print(f"Total winners: {len(winners)}\n")

# Collect genres & types from summaries (no extra HTTP requests)
type_counter: Counter = Counter()
for w in winners:
    if w.fanedit_type:
        type_counter[w.fanedit_type] += 1

print("By fanedit type:")
for ftype, n in type_counter.most_common():
    print(f"  {ftype}: {n}")

print("\nAll winners (most recent first):")
for w in winners:
    rating = f"editor={w.editor_rating}" if w.editor_rating else "unrated"
    print(f"  {w.release_date or '?':20s}  {w.title}")
    print(f"    [{w.fanedit_type}] by {w.faneditor} | {rating}")

# Fetch detail on highest-rated winner
rated = [w for w in winners if w.editor_rating]
if rated:
    best = max(rated, key=lambda w: w.editor_rating or 0)
    print(f"\n--- Highest-rated winner: {best.title} ---")
    detail = client.get_detail(best.url)
    print(f"  IMDB       : {detail.imdb_id}")
    print(f"  fanedit_id : {detail.fanedit_id}")
    print(f"  Editor rev : {len(detail.editor_reviews)}")
    print(f"  User rev   : {len(detail.user_reviews)}")
    print(f"  Awards     : {detail.awards}")
    print(f"  Synopsis   : {(detail.synopsis or '')[:300]}")
