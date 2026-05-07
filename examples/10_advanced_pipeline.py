"""10 — Advanced pipeline: export a category as JSONL with full detail.

Shows: iter_category(), model_dump_json(), error handling, polite crawling,
mediavocab round-trip, extra_fields inspection.
"""
import json
import time

from pyfanedit import FaneditClient, fanedit_to_release

CATEGORY = "extended"
SUMMARY_OUT = "extended_summaries.jsonl"
DETAIL_OUT = "extended_detail.jsonl"
MEDIAVOCAB_OUT = "extended_releases.jsonl"
MAX_DETAIL = 20   # set to None to fetch all (slow — one HTTP request per edit)

client = FaneditClient(cache_ttl=3600)

# --- Step 1: summaries (fast, one request per page) ---
print(f"Fetching '{CATEGORY}' summaries → {SUMMARY_OUT}")
summaries = []
with open(SUMMARY_OUT, "w") as f:
    for item in client.iter_category(CATEGORY):
        f.write(item.model_dump_json() + "\n")
        summaries.append(item)
print(f"  {len(summaries)} summaries\n")

# --- Step 2: full detail for first MAX_DETAIL entries ---
print(f"Fetching detail for first {MAX_DETAIL} → {DETAIL_OUT}")
details = []
with open(DETAIL_OUT, "w") as f:
    for summary in summaries[:MAX_DETAIL]:
        try:
            detail = client.get_detail(summary.url)
            f.write(detail.model_dump_json() + "\n")
            details.append(detail)
            # Inspect unmapped fields if any
            if detail.extra_fields:
                print(f"  extra_fields on {detail.slug}: {detail.extra_fields}")
        except Exception as exc:
            print(f"  SKIP {summary.url}: {exc}")
        time.sleep(0.5)
print(f"  {len(details)} details\n")

# --- Step 3: mediavocab Release objects ---
print(f"Converting to mediavocab → {MEDIAVOCAB_OUT}")
with open(MEDIAVOCAB_OUT, "w") as f:
    for detail in details:
        release = fanedit_to_release(detail)
        f.write(json.dumps(release.model_dump(mode="json")) + "\n")
print(f"  {len(details)} releases written")
