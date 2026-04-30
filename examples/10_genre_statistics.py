"""
User story: I'm curious about the landscape of fanediting — what genres,
franchises, and types dominate the IFDB?

Shows: iter_category across all categories, Counter analytics, no detail
fetches needed (summary data is enough).
"""
from collections import Counter

from pyfanedit import CATEGORIES, FaneditClient

client = FaneditClient()

type_counter: Counter = Counter()
franchise_counter: Counter = Counter()
release_year_counter: Counter = Counter()
total = 0

print("Scanning all IFDB categories for statistics (summaries only)...\n")

for cat_key in CATEGORIES:
    if cat_key == "unapproved":
        continue  # skip unapproved
    print(f"  Loading: {cat_key}")
    for item in client.iter_category(cat_key, max_pages=3):  # 3 pages = 150 per category
        total += 1
        if item.fanedit_type:
            type_counter[item.fanedit_type] += 1
        if item.franchise:
            franchise_counter[item.franchise] += 1
        if item.release_date:
            # extract year from "April 2026" or "2026"
            import re
            m = re.search(r"(20\d\d|19\d\d)", item.release_date)
            if m:
                release_year_counter[int(m.group(1))] += 1

print(f"\nTotal summaries scanned: {total}\n")

print("By fanedit type:")
for ftype, n in type_counter.most_common(10):
    bar = "█" * (n * 30 // max(type_counter.values()))
    print(f"  {ftype:<30} {n:5}  {bar}")

print("\nTop 20 franchises:")
for franchise, n in franchise_counter.most_common(20):
    bar = "█" * (n * 30 // max(franchise_counter.values()))
    print(f"  {franchise:<30} {n:5}  {bar}")

print("\nFanedits by release year:")
for year in sorted(release_year_counter):
    n = release_year_counter[year]
    bar = "█" * (n * 40 // max(release_year_counter.values()))
    print(f"  {year}  {n:4}  {bar}")
