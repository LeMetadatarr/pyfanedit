"""05 — Reviewer leaderboard and per-user review history.

Shows: get_reviewer_rank(), iter_user_reviews(), REVIEW_ORDER_CHOICES.
"""
from pyfanedit import FaneditClient

client = FaneditClient()

# --- Leaderboard (first page) ---
entries, _ = client.get_reviewer_rank()
print("Top 5 trusted reviewers\n")
for e in entries[:5]:
    print(f"  #{e.rank:>3}  {e.username:<20}  {e.review_count} reviews  "
          f"helpful: {e.helpful_yes} ({e.helpful_pct}%)")

# --- Per-user review history ---
top = entries[0]
print(f"\nHighest-rated picks by #{top.rank} {top.username}\n")
reviews, _ = client.get_user_reviews(top.user_id, order="rating")
for rv in reviews[:10]:
    print(f"  [{rv.ratings.overall:>4}]  {rv.fanedit_title}"
          f"  ({rv.fanedit_type or '?'})"
          f"  comments={rv.comment_count}")
