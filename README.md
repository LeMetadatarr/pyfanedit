# pyfanedit

Python scraping client for [fanedit.org](https://fanedit.org) (IFDB — the Internet Fanedit Database). Covers search, browsing, detail pages, reviewer leaderboards, news, and mediavocab export.

## Install

```bash
pip install pyfanedit            # plain requests — will warn and likely be blocked
pip install pyfanedit[stealth]   # recommended — adds curl_cffi for TLS bypass
```

fanedit.org uses TLS fingerprinting and Cloudflare heuristics. Without `[stealth]`, pyfanedit falls back to plain `requests` and emits a `RuntimeWarning` on every request. Most requests will be blocked.

## Quick Start

```python
from pyfanedit import FaneditClient

client = FaneditClient()

# search by keyword
results, _ = client.search("blade runner")
for r in results:
    print(r.title, r.faneditor, r.user_rating)

# fetch full detail
detail = client.get_detail(results[0].url)
print(detail.imdb_id, detail.genre, detail.time_cut)
```

## Transport

`PYFANEDIT_TRANSPORT` overrides auto-detection:

```bash
PYFANEDIT_TRANSPORT=curl_cffi   # explicit (default when curl_cffi is installed)
PYFANEDIT_TRANSPORT=requests    # force plain requests (warns)
```

Session injection — for tests, shared caches, or alternate profiles:

```python
import requests
from pyfanedit import FaneditClient
from pyfanedit.session import Session

# custom curl_cffi impersonation profile
client = FaneditClient(impersonate="chrome131")

# inject a plain requests.Session (e.g. for unit tests)
client = FaneditClient(session_factory=lambda **_: requests.Session())

# pre-built Session shared across clients
shared = Session(cache_ttl=900)
client = FaneditClient(session=shared)
```

## Public API

`FaneditClient` — `pyfanedit/client.py:34`

### Curated lists

| Method | Returns |
|---|---|
| `get_latest(page)` | Most recently added edits |
| `get_top_trusted_rated(page)` | Highest rated by trusted reviewers |
| `get_top_user_rated(page)` | Highest rated by all users |
| `get_most_popular(page)` | Most viewed |
| `get_award_winners(page)` | Fanedit of the Month winners |

All return `(list[FaneditSummary], next_url | None)`.

### Search and tag browsing

| Method | Signature |
|---|---|
| `search(keywords, scope, query_type, order, page)` | Keyword search — `pyfanedit/client.py:99` |
| `iter_search(keywords, ...)` | Paginating generator — `pyfanedit/client.py:131` |
| `search_by_original_title(title, order)` | Exact match on source film title — `pyfanedit/client.py:209` |
| `get_by_tag(tag_type, tag_value, page)` | Browse by franchise, editor name, year, award, … — `pyfanedit/client.py:153` |
| `iter_by_tag(tag_type, tag_value, max_pages)` | Paginating generator — `pyfanedit/client.py:171` |
| `get_category(category, page)` | Named category (`fanfix`, `extended`, `tv_to_movie`, …) — `pyfanedit/client.py:70` |
| `iter_category(category, max_pages)` | Paginating generator — `pyfanedit/client.py:85` |

`ORDER_CHOICES`: `rdate` (default), `date`, `modified`, `alpha`, `rratio`, `rvote`.

### Detail

| Method | Signature |
|---|---|
| `get_detail(url)` | Full page by URL or slug — `pyfanedit/client.py:232` |
| `get_detail_by_slug(slug)` | Convenience wrapper — `pyfanedit/client.py:244` |

### Reviews and reviewer leaderboard

| Method | Signature |
|---|---|
| `get_reviewer_rank(page)` | Leaderboard, ~50 entries/page — `pyfanedit/client.py:258` |
| `iter_reviewer_rank(max_pages)` | Paginating generator — `pyfanedit/client.py:267` |
| `get_user_reviews(user_id, page, order)` | All reviews by one user — `pyfanedit/client.py:296` |
| `iter_user_reviews(user_id, order, max_pages)` | Paginating generator — `pyfanedit/client.py:318` |
| `get_latest_user_reviews(page)` | Latest-reviews feed (all users) — `pyfanedit/client.py:327` |
| `get_latest_trusted_reviews(page)` | Latest trusted-reviewer feed — `pyfanedit/client.py:332` |

`REVIEW_ORDER_CHOICES`: `rdate`, `date`, `rating`, `rrating`, `updated`, `helpful`, `rhelpful`, `discussed`.

### News

| Method | Signature |
|---|---|
| `get_news()` | Front-page article cards (~15) — `pyfanedit/client.py:341` |
| `get_news_article(url)` | Full article body + mentioned fanedit URLs — `pyfanedit/client.py:347` |

## mediavocab integration

`fanedit_to_release` — `pyfanedit/converters.py:166` — converts a `FaneditSummary` or `FaneditDetail` to a typed `mediavocab.Release`:

```python
from pyfanedit import FaneditClient, fanedit_to_release

client = FaneditClient()
summaries = client.search_by_original_title("Star Wars")

for summary in summaries[:3]:
    detail = client.get_detail(summary.url)
    release = fanedit_to_release(detail)
    work = release.work

    print(work.title, work.variant_kind, work.runtime)
    print(work.external_ids.get("derived_from_imdb"))  # source IMDb id
```

Key mappings:

| IFDB field | mediavocab destination |
|---|---|
| `faneditor` | `Work.credits` — `RelationRole.EDITOR` |
| `fanedit_type` | `Work.variant_kind` (`FANEDIT` / `EXTENDED` / `TV_TO_MOVIE` / `MOVIE_TO_TV` / `PRESERVATION`) |
| `fanedit_running_time` | `Work.runtime` (seconds) |
| `release_information` | `Work.source_format` (e.g. `BD-25`, `WEB-DL`) |
| `available_in` | `Release.resolution`, `Release.hdr`, `Release.audio_channels` |
| `imdb_id` | `Work.external_ids["derived_from_imdb"]` |
| Source film backlink | `Work.extra["work_relations"]` — `WorkRelation(kind=FANEDIT_OF, target=<source Work>)` |

`MOVIE_TO_TV` recuts produce `MediaType.EPISODIC_SERIES` per the mediavocab "one Work, one MediaType" axiom.

## Documentation

- [Getting Started](docs/getting-started.md)
- [FaneditClient Reference](docs/reference.md)
- [Models](docs/models.md)
- [Transport and Session Injection](docs/transport.md)
- [mediavocab Converter](docs/converter.md)
- [IDs and Metadata](docs/ids-and-metadata.md)

## License

Apache 2.0
