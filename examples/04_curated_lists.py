"""04 — Curated lists: latest, popular, top-rated, award winners.

Shows: get_latest(), get_most_popular(), get_top_trusted_rated(),
get_top_user_rated(), get_award_winners().
"""
from pyfanedit import FaneditClient

client = FaneditClient()

sections = [
    ("Latest",              client.get_latest),
    ("Most Popular",        client.get_most_popular),
    ("Top Trusted Rated",   client.get_top_trusted_rated),
    ("Top User Rated",      client.get_top_user_rated),
    ("Award Winners",       client.get_award_winners),
]

for label, method in sections:
    items, _ = method()
    print(f"\n=== {label} (first 5) ===")
    for item in items[:5]:
        print(f"  [{item.editor_rating or '?':>4} / {item.user_rating or '?'}] "
              f"{item.title}  by {item.faneditor}")
