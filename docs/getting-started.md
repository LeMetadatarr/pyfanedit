# Getting Started

## Install

```bash
pip install pyfanedit[stealth]   # recommended — curl_cffi for TLS bypass
pip install pyfanedit            # plain requests — will warn and likely be blocked
```

For a dev install:

```bash
git clone https://github.com/OpenJarbas/pyfanedit
cd pyfanedit
pip install -e ".[test]"
```

## First Search

```python
from pyfanedit import FaneditClient

client = FaneditClient()
results, next_page = client.search("batman")
for r in results:
    print(r.title, r.faneditor, r.release_date, r.user_rating)
```

`search` returns `(list[FaneditSummary], next_page_url | None)`. — `pyfanedit/client.py:99`

## Get Full Detail

Listing pages return lightweight `FaneditSummary` objects. Call `get_detail` to get the full record — genre, cuts, intention, IMDB ID, and embedded reviews:

```python
results, _ = client.search("blade runner")
detail = client.get_detail(results[0].url)

print(detail.genre)
print(detail.imdb_id)
print(detail.time_cut)
print(len(detail.user_reviews))
```

`get_detail` accepts a full URL or a bare slug. — `pyfanedit/client.py:232`

## Browse Categories

```python
# fanfix, fanmix, extended, tv_to_movie, movie_to_tv, shorts, special, documentary, preservation, unapproved
items, next_page = client.get_category("fanfix")
```

## Pagination

All list-returning methods have an `iter_*` counterpart that fetches pages automatically:

```python
for edit in client.iter_search("marvel", max_pages=3):
    print(edit.title)

for edit in client.iter_category("extended", max_pages=2):
    print(edit.title)

for edit in client.iter_by_tag("franchise", "star-wars"):
    print(edit.title)
```

`max_pages=0` (the default) means no limit.

## Common Pitfalls

**Rate limiting.** No published limits — add a small sleep when iterating many pages:

```python
import time
for edit in client.iter_category("fanfix"):
    print(edit.title)
    time.sleep(0.5)
```

**Lazy cover images.** `cover_url` may be `None` when the page stores only a `data:` placeholder. Always guard.

**`imdb_id` not guaranteed.** `FaneditDetail.imdb_id` is extracted from the first IMDB link on the page. If absent or malformed, the value is `None`.

**`fanedit_id` is detail-only.** The WordPress post ID is extracted from a `<body class="postid-NNN">` element that only appears on individual detail pages. It is always `None` on `FaneditSummary`. — `pyfanedit/parsers.py:85`

## See also

- [FaneditClient Reference](reference.md)
- [Models](models.md)
- [Transport and Session Injection](transport.md)
