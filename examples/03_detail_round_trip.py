"""03 — List → detail → reviews round trip.

Shows: iter_search(), get_detail(), Review and ReviewRatings fields,
cuts_and_additions, intention.
"""
from pyfanedit import FaneditClient

client = FaneditClient()

summaries = list(client.iter_search("the matrix", max_pages=2))
print(f"Found {len(summaries)} summaries\n")

# Fetch detail for the first result with a user rating
for summary in summaries:
    if summary.user_rating is not None:
        detail = client.get_detail(summary.url)
        break
else:
    print("No rated results found")
    raise SystemExit

print(f"{detail.title}")
print(f"  genre          : {', '.join(detail.genre or [])}")
print(f"  imdb_id        : {detail.imdb_id}")
print(f"  time_cut       : {detail.time_cut}")
print(f"  intention      : {(detail.intention or '')[:120]}")
print(f"  cuts snippet   : {(detail.cuts_and_additions or '')[:200]}")

print(f"\n  {len(detail.editor_reviews)} editor review(s)")
for rv in detail.editor_reviews[:2]:
    print(f"    {rv.reviewer}  overall={rv.ratings.overall}"
          f"  narrative={rv.ratings.narrative}  enjoyment={rv.ratings.enjoyment}")

print(f"\n  {len(detail.user_reviews)} user review(s)")
for rv in detail.user_reviews[:3]:
    print(f"    {rv.reviewer}  overall={rv.ratings.overall}  helpful={rv.helpful_yes}")
