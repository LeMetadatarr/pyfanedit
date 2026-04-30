"""
User story: I have a list of IMDB IDs and want to know which fanedits exist
for each film.

Shows: search by original movie title, imdb_id extraction, building a
reverse index {imdb_id → [FaneditDetail]}.

Requires: a list of movie titles or IMDB IDs you already know.
"""
from collections import defaultdict

from pyfanedit import FaneditClient

client = FaneditClient()

# --- Input: movies you care about ---
MOVIES = [
    "Blade Runner",
    "The Dark Knight",
    "Star Wars",
    "Dune",
    "The Matrix",
]

imdb_index: dict[str, list] = defaultdict(list)
no_imdb: list = []

for movie in MOVIES:
    print(f"\nSearching: {movie}")
    results, _ = client.search(movie, scope="title", query_type="any")
    for summary in results:
        detail = client.get_detail(summary.url)
        if detail.imdb_id:
            imdb_index[detail.imdb_id].append({
                "title": detail.title,
                "url": detail.url,
                "fanedit_id": detail.fanedit_id,
                "editor_rating": detail.editor_rating,
                "user_rating": detail.user_rating,
                "fanedit_type": detail.fanedit_type,
                "faneditor": detail.faneditor,
            })
            print(f"  {detail.imdb_id}  {detail.title}")
        else:
            no_imdb.append(detail.title)

print("\n\n=== IMDB → Fanedits index ===")
for imdb_id, edits in sorted(imdb_index.items()):
    print(f"\n{imdb_id}  ({len(edits)} fanedits)")
    for e in sorted(edits, key=lambda x: x["editor_rating"] or 0, reverse=True):
        rating = f"{e['editor_rating']:.1f}" if e["editor_rating"] else "  - "
        print(f"  [{rating}] {e['title']}  ({e['fanedit_type']})")

if no_imdb:
    print(f"\nNo IMDB link found for {len(no_imdb)} edits:")
    for t in no_imdb:
        print(f"  - {t}")
