"""
User story: I'm building a production scraper and need control over
TLS impersonation, caching, and rate limiting.

Shows: custom Session, multiple impersonation profiles, cache inspection,
polite crawling with delays.
"""
import time

from pyfanedit import FaneditClient
from pyfanedit.session import Session

# --- Option A: configure via FaneditClient constructor ---
client = FaneditClient(
    impersonate="chrome124",   # any curl_cffi impersonation target
    cache_ttl=600.0,           # 10-minute cache
)

# --- Option B: build a Session manually and pass it ---
session = Session(
    impersonate="safari17_0",
    cache_ttl=0,       # disable cache entirely (always fresh)
    cache_size=0,
)

# Attach the custom session to a client
from pyfanedit.parsers import parse_listing_page

def polite_search(keywords: str, delay: float = 1.0):
    """Search with a per-request delay."""
    page = 1
    while True:
        html = session.get(
            "fanedit-search/search-results/",
            params={"query": "all", "scope": "title", "keywords": keywords, "order": "rdate", "pg": page},
        )
        items, next_url = parse_listing_page(html)
        yield from items
        if not next_url:
            break
        page += 1
        time.sleep(delay)

print("Polite search with 1s delay between pages:\n")
for i, item in enumerate(polite_search("Lord of the Rings")):
    print(f"  {i+1:3}. {item.title}  ({item.release_date})")
    if i >= 9:
        print("  ... (stopping at 10 for demo)")
        break

# --- Cache hit demonstration ---
print("\nCache demonstration:")
client2 = FaneditClient(cache_ttl=300.0)

t0 = time.time()
items1, _ = client2.get_category("fanfix", page=1)
t1 = time.time()

items2, _ = client2.get_category("fanfix", page=1)  # should hit cache
t2 = time.time()

print(f"  First request:  {t1-t0:.3f}s  ({len(items1)} items)")
print(f"  Cached request: {t2-t1:.4f}s  ({len(items2)} items)  ← from cache")
