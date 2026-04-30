"""
User story: I want a local dataset of all FanFix edits to analyse offline.

Shows: iter_category, model.model_dump(), JSONL export, progress reporting.

Output: fanfix_edits.jsonl  (one JSON object per line, summaries only)
        fanfix_detail.jsonl (full detail including reviews — slower, one HTTP
                             request per fanedit, use max_items to limit)
"""
import json
import sys
import time

from pyfanedit import FaneditClient

SUMMARY_OUT = "fanfix_edits.jsonl"
DETAIL_OUT = "fanfix_detail.jsonl"
MAX_DETAIL = 20  # set to None to fetch all (slow — 1 300+ requests)

client = FaneditClient(cache_ttl=0)  # disable cache for fresh data

# --- Step 1: summaries (fast, ~26 pages) ---
print(f"Fetching FanFix summaries → {SUMMARY_OUT}")
count = 0
with open(SUMMARY_OUT, "w") as f:
    for item in client.iter_category("fanfix"):
        f.write(json.dumps(item.model_dump()) + "\n")
        count += 1
        if count % 50 == 0:
            print(f"  {count} summaries written...")
            sys.stdout.flush()

print(f"Done: {count} summaries.\n")

# --- Step 2: full details (slow — throttle with a small sleep) ---
limit = MAX_DETAIL or count
print(f"Fetching full detail for up to {limit} edits → {DETAIL_OUT}")

with open(SUMMARY_OUT) as fin, open(DETAIL_OUT, "w") as fout:
    for i, line in enumerate(fin):
        if i >= limit:
            break
        summary = json.loads(line)
        try:
            detail = client.get_detail(summary["url"])
            fout.write(json.dumps(detail.model_dump()) + "\n")
            print(f"  [{i+1}/{limit}] {detail.title}")
        except Exception as e:
            print(f"  [{i+1}/{limit}] ERROR {summary['url']}: {e}", file=sys.stderr)
        time.sleep(0.5)  # be polite

print(f"\nDone. Check {SUMMARY_OUT} and {DETAIL_OUT}.")
