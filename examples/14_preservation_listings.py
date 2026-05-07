"""
User story: I'm interested in film preservation — show me all preservation
projects with their IMDB IDs so I can cross-reference against other databases.

Shows: iter_category("preservation"), get_detail() for IMDB IDs,
CSV export for use in spreadsheets.
"""
import csv

from pyfanedit import FaneditClient

client = FaneditClient()

OUTPUT_CSV = "preservation_projects.csv"

print("Loading all preservation listings...\n")
summaries = list(client.iter_category("preservation"))
print(f"Found {len(summaries)} preservation projects.\n")

rows = []
for i, summary in enumerate(summaries, 1):
    print(f"  [{i}/{len(summaries)}] {summary.title}")
    detail = client.get_detail(summary.url)
    rows.append({
        "fanedit_id": detail.fanedit_id,
        "slug": detail.slug,
        "title": detail.title,
        "faneditor": detail.faneditor,
        "original_title": detail.original_title,
        "original_release_date": detail.original_release_date,
        "imdb_id": detail.imdb_id or "",
        "imdb_url": f"https://www.imdb.com/title/{detail.imdb_id}/" if detail.imdb_id else "",
        "fanedit_release_date": detail.fanedit_release_date,
        "fanedit_running_time": detail.fanedit_running_time,
        "available_in": detail.available_in,
        "editor_rating": detail.editor_rating or "",
        "user_rating": detail.user_rating or "",
        "url": detail.url,
    })

# Write CSV
fieldnames = list(rows[0].keys()) if rows else []
with open(OUTPUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nExported {len(rows)} rows to {OUTPUT_CSV}")

# Quick stats
with_imdb = sum(1 for r in rows if r["imdb_id"])
print(f"IMDB IDs found: {with_imdb}/{len(rows)} ({100*with_imdb//len(rows) if rows else 0}%)")

rated = [r for r in rows if r["editor_rating"]]
print(f"Trusted-reviewer rated: {len(rated)}/{len(rows)}")
