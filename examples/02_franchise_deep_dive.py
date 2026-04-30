"""
User story: I'm a Star Wars fan — show me every fanedit in the franchise,
sorted by trusted reviewer rating, with full metadata.

Shows: franchise tag browsing, iter_by_tag, sort order, detail enrichment.
"""
from pyfanedit import FaneditClient

client = FaneditClient()

franchise = "star-wars"
print(f"All fanedits in the '{franchise}' franchise (sorted by trusted reviewer rating)\n")

# iter_by_tag handles pagination automatically
summaries = list(client.iter_by_tag("franchise", franchise))
print(f"Total: {len(summaries)} fanedits\n")

# Sort locally by editor rating (highest first, unrated last)
rated = sorted(
    [s for s in summaries if s.editor_rating],
    key=lambda s: s.editor_rating or 0,
    reverse=True,
)
unrated = [s for s in summaries if not s.editor_rating]

print("Top 10 by trusted reviewer rating:")
for i, s in enumerate(rated[:10], 1):
    print(f"  {i:2}. [{s.editor_rating:4.1f}] {s.title}")
    print(f"        by {s.faneditor} | {s.fanedit_type} | {s.release_date}")

print(f"\n{len(unrated)} fanedits have no trusted reviewer rating yet.")

# Fetch full detail for #1 to show IMDB mapping
if rated:
    best = client.get_detail(rated[0].url)
    print(f"\n--- Detail: #{1} ---")
    print(f"  Title      : {best.title}")
    print(f"  IMDB       : https://www.imdb.com/title/{best.imdb_id}/")
    print(f"  fanedit_id : {best.fanedit_id}")
    print(f"  Editor rev : {len(best.editor_reviews)}  User rev: {len(best.user_reviews)}")
    if best.editor_reviews:
        r = best.editor_reviews[0]
        print(f"  Top review : {r.reviewer} ({r.reviewer_rank}) — {r.ratings.overall}/10")
        print(f"    {(r.body or '')[:200]}")
