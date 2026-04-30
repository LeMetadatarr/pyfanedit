"""
User story: I discovered a faneditor whose work I love. Show me everything
they've made, with ratings and synopsis.

Shows: get_by_tag("faneditorname", ...), detail enrichment, portfolio summary.
"""
from pyfanedit import FaneditClient

client = FaneditClient()

# URL-slug form of the faneditor's name (lowercase, hyphens for spaces)
FANEDITOR_SLUG = "neglify"

print(f"Portfolio: {FANEDITOR_SLUG}\n")

works = list(client.iter_by_tag("faneditorname", FANEDITOR_SLUG))
print(f"{len(works)} fanedits listed\n")

# Enrich with detail (ratings + synopsis)
detailed = []
for summary in works:
    detail = client.get_detail(summary.url)
    detailed.append(detail)

# Sort by editor rating desc, unrated last
detailed.sort(key=lambda d: d.editor_rating or -1, reverse=True)

# Print portfolio
type_counts: dict[str, int] = {}
for d in detailed:
    ftype = d.fanedit_type or "Unknown"
    type_counts[ftype] = type_counts.get(ftype, 0) + 1

    rating_str = (
        f"editor={d.editor_rating:.1f}  user={d.user_rating}"
        if d.editor_rating else "not yet rated"
    )
    print(f"  {d.title}")
    print(f"    [{ftype}] {d.fanedit_release_date} | {rating_str}")
    if d.imdb_id:
        print(f"    IMDB: https://www.imdb.com/title/{d.imdb_id}/")
    if d.synopsis:
        print(f"    {d.synopsis[:150]}")
    print()

print("--- Summary ---")
for ftype, n in sorted(type_counts.items()):
    print(f"  {ftype}: {n}")
rated = [d for d in detailed if d.editor_rating]
if rated:
    avg = sum(d.editor_rating for d in rated) / len(rated)
    print(f"  Average trusted-reviewer rating: {avg:.2f}")
