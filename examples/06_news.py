"""06 — News: article cards and full article bodies.

Shows: get_news(), get_news_article(), mentioned_fanedit_urls, get_detail().
"""
from pyfanedit import FaneditClient

client = FaneditClient()

articles = client.get_news()
print(f"News front page: {len(articles)} articles\n")

for card in articles[:5]:
    date = (card.published_at or "")[:10]
    print(f"  [{date}] {card.title}  by {card.author}")

# Fetch the most recent article in full
latest = articles[0]
print(f"\n--- Full article: {latest.title} ---\n")
full = client.get_news_article(latest.url)
print(f"Views      : {full.views}")
print(f"Category   : {full.category}")
print(f"Body snippet: {(full.body_text or '')[:300]}\n")

# Fanedit links mentioned in the article body
if full.mentioned_fanedit_urls:
    print(f"Mentioned fanedits ({len(full.mentioned_fanedit_urls)}):")
    for url in full.mentioned_fanedit_urls[:5]:
        detail = client.get_detail(url)
        print(f"  {detail.title}  [{detail.user_rating}]")
else:
    print("No fanedit links in this article.")
