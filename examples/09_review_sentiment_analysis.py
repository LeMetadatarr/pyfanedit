"""
User story: I want to understand how reviewers score fanedits across
dimensions — do high-rated edits score consistently across all criteria,
or do some dimensions drag the average down?

Shows: get_top_trusted_rated(), get_detail() reviews, dimension statistics.
No external libraries needed — pure stdlib math.
"""
import statistics
from collections import defaultdict

from pyfanedit import FaneditClient

client = FaneditClient()

TOP_N = 10  # fetch detail for top N fanedits only

print(f"Review dimension analysis — top {TOP_N} trusted-reviewer rated fanedits\n")

top, _ = client.get_top_trusted_rated()

dimension_scores: dict[str, list[float]] = {
    "overall": [],
    "audio_video_quality": [],
    "audio_editing": [],
    "visual_editing": [],
    "narrative": [],
    "enjoyment": [],
}

records = []
for summary in top[:TOP_N]:
    detail = client.get_detail(summary.url)
    all_reviews = detail.editor_reviews + detail.user_reviews
    for rv in all_reviews:
        r = rv.ratings
        row = {
            "fanedit": detail.title,
            "reviewer": rv.reviewer,
            "overall": r.overall,
            "audio_video_quality": r.audio_video_quality,
            "audio_editing": r.audio_editing,
            "visual_editing": r.visual_editing,
            "narrative": r.narrative,
            "enjoyment": r.enjoyment,
        }
        records.append(row)
        for dim in dimension_scores:
            val = getattr(r, dim)
            if val is not None:
                dimension_scores[dim].append(val)
    print(f"  {detail.title}: {len(all_reviews)} reviews")

print(f"\nTotal review records collected: {len(records)}\n")

print("Dimension averages (across all reviews):")
print(f"  {'Dimension':<25} {'Mean':>6}  {'Stdev':>6}  {'Min':>5}  {'Max':>5}  {'N':>5}")
print(f"  {'-'*25}  {'-'*6}  {'-'*6}  {'-'*5}  {'-'*5}  {'-'*5}")
for dim, scores in dimension_scores.items():
    if not scores:
        continue
    mean = statistics.mean(scores)
    stdev = statistics.stdev(scores) if len(scores) > 1 else 0.0
    print(
        f"  {dim:<25}  {mean:6.2f}  {stdev:6.2f}  {min(scores):5.1f}  {max(scores):5.1f}  {len(scores):5}"
    )

# Per-fanedit: which dimension scores lowest on average?
print("\nPer-fanedit weakest dimension:")
by_fanedit: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
for row in records:
    for dim in dimension_scores:
        v = row.get(dim)
        if v is not None:
            by_fanedit[row["fanedit"]][dim].append(v)

for title, dims in by_fanedit.items():
    avgs = {d: statistics.mean(vs) for d, vs in dims.items() if vs}
    if avgs:
        weakest = min(avgs, key=avgs.get)
        strongest = max(avgs, key=avgs.get)
        print(f"  {title[:45]:<45}  weakest={weakest} ({avgs[weakest]:.1f})  "
              f"strongest={strongest} ({avgs[strongest]:.1f})")
