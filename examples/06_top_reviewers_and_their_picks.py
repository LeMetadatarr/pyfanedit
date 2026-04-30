"""
User story: I want to know what the most respected reviewers think are the
best fanedits — trust the critics, not the crowd.

Shows: get_reviewer_rank(), get_user_reviews() with order="rating",
cross-referencing reviewer rank with their highest-rated edits.
"""
from pyfanedit import FaneditClient

client = FaneditClient()

TOP_N_REVIEWERS = 5
REVIEWS_PER_REVIEWER = 5

print(f"Top {TOP_N_REVIEWERS} reviewers and their highest-rated picks\n")

leaderboard, _ = client.get_reviewer_rank()
top_reviewers = leaderboard[:TOP_N_REVIEWERS]

for reviewer in top_reviewers:
    print(f"#{reviewer.rank} {reviewer.username}")
    print(f"   {reviewer.review_count} reviews | "
          f"helpful: {reviewer.helpful_yes} ({reviewer.helpful_pct}%)")

    # Fetch their highest-rated reviews
    reviews, _ = client.get_user_reviews(reviewer.user_id, order="rating")
    print(f"   Top {REVIEWS_PER_REVIEWER} picks:")
    for rv in reviews[:REVIEWS_PER_REVIEWER]:
        dims = (
            f"av={rv.ratings.audio_video_quality} "
            f"ae={rv.ratings.audio_editing} "
            f"vis={rv.ratings.visual_editing} "
            f"nar={rv.ratings.narrative} "
            f"enj={rv.ratings.enjoyment}"
        )
        print(f"     [{rv.ratings.overall:4.1f}] {rv.fanedit_title} ({rv.fanedit_type})")
        print(f"            {dims}")
    print()
