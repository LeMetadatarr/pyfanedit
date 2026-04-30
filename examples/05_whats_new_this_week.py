"""
User story: I check fanedit.org every week for new releases. Show me what
came out recently with a clean summary, no forum login required.

Shows: get_news(), get_news_article(), mentioned_fanedit_urls, get_detail().
"""
from pyfanedit import FaneditClient

client = FaneditClient()

print("Fetching news front page...\n")
articles = client.get_news()

for article in articles[:5]:
    date = (article.published_at or "")[:10]
    print(f"[{date}] {article.title}")
    print(f"  by {article.author} | {article.reading_time}")
    print(f"  {article.url}")

# Pick the most recent article and extract the fanedits it mentions
latest = articles[0]
print(f"\n--- Fetching full article: {latest.title} ---\n")
full = client.get_news_article(latest.url)

print(f"Views: {full.views}")
print(f"Body preview: {(full.body_text or '')[:400]}\n")

if not full.mentioned_fanedit_urls:
    print("No IFDB fanedit links found in this article.")
else:
    print(f"Fanedits mentioned ({len(full.mentioned_fanedit_urls)}):\n")
    for url in full.mentioned_fanedit_urls:
        detail = client.get_detail(url)
        rating = (
            f"editor={detail.editor_rating} user={detail.user_rating}"
            if detail.editor_rating
            else "not yet rated"
        )
        print(f"  {detail.title}")
        print(f"    [{detail.fanedit_type}] by {detail.faneditor} | {detail.fanedit_release_date}")
        print(f"    {rating}")
        if detail.imdb_id:
            print(f"    IMDB: https://www.imdb.com/title/{detail.imdb_id}/")
        print(f"    {detail.synopsis[:120] if detail.synopsis else ''}")
        print()
