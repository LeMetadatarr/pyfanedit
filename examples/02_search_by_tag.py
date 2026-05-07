"""02 — Browse by tag: franchise, editor, year, award.

Shows: get_by_tag(), iter_by_tag(), common tag_type values.
"""
from pyfanedit import FaneditClient

client = FaneditClient()

# --- franchise tag ---
print("Star Wars franchise fanedits (first page)\n")
items, next_page = client.get_by_tag("franchise", "star-wars")
for item in items[:10]:
    print(f"  [{item.editor_rating or '?':>4}] {item.title}  by {item.faneditor}")

# --- editor tag ---
print("\nAll fanedits by 'neglify' (paginated)\n")
portfolio = list(client.iter_by_tag("faneditorname", "neglify"))
print(f"  Total: {len(portfolio)}")
for item in portfolio:
    print(f"  {item.title}  ({item.fanedit_type})")

# --- award tag ---
print("\nFanedit of the Month winners (first page)\n")
winners, _ = client.get_award_winners()
for w in winners[:5]:
    print(f"  {w.title}  — {w.faneditor}  [{w.editor_rating}]")
