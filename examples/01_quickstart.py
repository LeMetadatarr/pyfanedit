"""01 — Quickstart: search and fetch a detail page.

Shows: FaneditClient construction, search(), get_detail(), common fields.
"""
from pyfanedit import FaneditClient

client = FaneditClient()

results, next_page = client.search("blade runner")
print(f"Found {len(results)} results  (next page: {bool(next_page)})\n")

for r in results[:5]:
    print(f"  [{r.fanedit_type}] {r.title}")
    print(f"    by {r.faneditor}  |  released {r.release_date}  |  user_rating {r.user_rating}")

# Fetch full detail for the first result
if results:
    detail = client.get_detail(results[0].url)
    print(f"\n--- {detail.title} ---")
    print(f"  fanedit_id : {detail.fanedit_id}")
    print(f"  imdb_id    : {detail.imdb_id}")
    print(f"  genre      : {', '.join(detail.genre or [])}")
    print(f"  time_cut   : {detail.time_cut}")
    print(f"  reviews    : {len(detail.user_reviews)} user  /  {len(detail.editor_reviews)} editor")
