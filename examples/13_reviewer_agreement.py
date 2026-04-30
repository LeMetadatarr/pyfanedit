"""
User story: How much do the top trusted reviewers agree with each other?
Find fanedits reviewed by multiple top-10 reviewers and compare their scores.

Shows: iter_reviewer_rank(), iter_user_reviews(), cross-referencing reviews
across reviewers by fanedit URL.
"""
from collections import defaultdict

from pyfanedit import FaneditClient

client = FaneditClient()

TOP_N = 10  # top N reviewers to compare

print(f"Loading top {TOP_N} reviewers from leaderboard...\n")
leaderboard, _ = client.get_reviewer_rank()
top = leaderboard[:TOP_N]

# Map: fanedit_url → {username: overall_rating}
fanedit_ratings: dict[str, dict[str, float]] = defaultdict(dict)

for reviewer in top:
    print(f"  Fetching reviews for #{reviewer.rank} {reviewer.username} "
          f"({reviewer.review_count} reviews, loading page 1 only)...")
    reviews, _ = client.get_user_reviews(reviewer.user_id, order="rating")
    for rv in reviews:
        if rv.ratings.overall is not None:
            fanedit_ratings[rv.fanedit_url][reviewer.username] = rv.ratings.overall

# Find fanedits rated by 3+ of the top reviewers
multi_rated = {
    url: ratings
    for url, ratings in fanedit_ratings.items()
    if len(ratings) >= 3
}

print(f"\nFanedits rated by 3+ of the top {TOP_N} reviewers: {len(multi_rated)}\n")

import statistics

rows = []
for url, ratings in multi_rated.items():
    scores = list(ratings.values())
    mean = statistics.mean(scores)
    spread = max(scores) - min(scores)
    rows.append((spread, mean, url, ratings))

# Sort by spread (most disagreement first)
rows.sort(reverse=True)

print("Most controversial (highest score spread):")
print(f"  {'Spread':>6}  {'Mean':>6}  {'Reviewers':>3}  URL")
for spread, mean, url, ratings in rows[:15]:
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    reviewers_str = "  ".join(f"{u}={v:.0f}" for u, v in sorted(ratings.items()))
    print(f"  {spread:6.1f}  {mean:6.2f}  {len(ratings):3}  {slug}")
    print(f"         {reviewers_str}")

print("\nMost agreed upon (lowest spread, 3+ reviews):")
rows_agreed = sorted(rows, key=lambda r: r[0])
for spread, mean, url, ratings in rows_agreed[:10]:
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    print(f"  spread={spread:.1f}  mean={mean:.2f}  ({len(ratings)} reviewers)  {slug}")
