"""
User story: I want to find all fanedits of a specific movie.

Shows: keyword search, pagination, detail fetch, IMDB ID extraction.
"""
from pyfanedit import FaneditClient

client = FaneditClient()

movie = "Blade Runner"
print(f"Searching for fanedits of: {movie}\n")

results = list(client.iter_search(movie, max_pages=2))
print(f"Found {len(results)} results (first 2 pages)\n")

for item in results:
    rating = f"editor={item.editor_rating} user={item.user_rating}" if item.editor_rating else "unrated"
    print(f"  [{item.fanedit_type}] {item.title}")
    print(f"    by {item.faneditor} | {item.release_date} | {rating}")
    print(f"    {item.url}")

# Get full detail for the first result
if results:
    print(f"\n--- Full detail: {results[0].title} ---")
    detail = client.get_detail(results[0].url)
    print(f"  fanedit_id : {detail.fanedit_id}   (stable WordPress post ID)")
    print(f"  slug       : {detail.slug}")
    print(f"  imdb_id    : {detail.imdb_id}")
    print(f"  genre      : {', '.join(detail.genre or [])}")
    print(f"  franchise  : {', '.join(detail.franchise or [])}")
    print(f"  original   : {detail.original_title} ({detail.original_release_date})")
    print(f"  runtime    : {detail.original_running_time} → {detail.fanedit_running_time}")
    print(f"  cut        : {detail.time_cut}  added: {detail.time_added}")
    print(f"  synopsis   : {(detail.synopsis or '')[:200]}")
    print(f"  awards     : {detail.awards}")
