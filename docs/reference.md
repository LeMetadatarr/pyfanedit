# FaneditClient Reference

`pyfanedit/client.py:34`

Single entry point for all fanedit.org interactions. Wraps a `Session` internally.

## Constructor

```python
FaneditClient(
    impersonate: str = "chrome120",
    cache_ttl: float = 300.0,
    session: Session | None = None,
    session_factory: callable | None = None,
)
```

| Parameter | Default | Description |
|---|---|---|
| `impersonate` | `"chrome120"` | curl_cffi browser profile for TLS fingerprinting |
| `cache_ttl` | `300.0` | Seconds before a cached URL expires; `0` disables caching |
| `session` | `None` | Pre-built `Session` instance (ignores `impersonate` and `cache_ttl`) |
| `session_factory` | `None` | Callable returning the underlying HTTP session |

See [Transport and Session Injection](transport.md) for injection patterns.

---

## Curated Lists

All methods: `(page: int = 1) -> tuple[list[FaneditSummary], str | None]`

| Method | URL path | Description |
|---|---|---|
| `get_latest` | `latest-ifdb-fanedits/` | Most recently added edits — `pyfanedit/client.py:186` |
| `get_top_trusted_rated` | `top-trusted-reviewer-rated-fanedits/` | Highest rated by trusted reviewers — `pyfanedit/client.py:190` |
| `get_top_user_rated` | `top-user-rated-fanedits/` | Highest rated by all users — `pyfanedit/client.py:194` |
| `get_most_popular` | `most-popular/` | Most viewed — `pyfanedit/client.py:198` |
| `get_award_winners` | tag `award/fanedit-of-the-month` | Fanedit of the Month winners — `pyfanedit/client.py:202` |

```python
items, next_page = client.get_top_user_rated()
items, next_page = client.get_award_winners(page=2)
```

---

## Search

### `search`

`pyfanedit/client.py:99`

```python
search(
    keywords: str,
    scope: str = "title",
    query_type: str = "all",
    order: str = "rdate",
    page: int = 1,
) -> tuple[list[FaneditSummary], str | None]
```

| Parameter | Values | Description |
|---|---|---|
| `scope` | `"title"` / `"reviews"` | Where to match keywords |
| `query_type` | `"all"` / `"any"` / `"exact"` | Boolean logic for multi-word queries |
| `order` | see `ORDER_CHOICES` | Sort order |

### `iter_search`

`pyfanedit/client.py:131` — same parameters as `search` except `page` is managed internally; `max_pages=0` means no limit.

### `search_by_original_title`

`pyfanedit/client.py:209`

```python
search_by_original_title(title: str, *, order: str = "rdate") -> list[FaneditSummary]
```

Exact match on `FaneditSummary.original_title`. Runs an exact-phrase search then filters results locally. Preferred over `search` when looking up all fanedits of a specific film — `"Alien"` will not return `"Aliens"` recuts.

### `ORDER_CHOICES`

`pyfanedit/client.py:31`

| Value | Sort order |
|---|---|
| `rdate` | Fanedit release date, newest first (default) |
| `date` | Date added to IFDB, newest first |
| `modified` | Last modified, newest first |
| `alpha` | A–Z by title |
| `rratio` | Highest trusted-reviewer rating first |
| `rvote` | Most user votes first |

---

## Tag and Franchise Browsing

### `get_by_tag`

`pyfanedit/client.py:153`

```python
get_by_tag(tag_type: str, tag_value: str, page: int = 1) -> tuple[list[FaneditSummary], str | None]
```

| `tag_type` | Example `tag_value` |
|---|---|
| `franchise` | `"star-wars"` |
| `faneditorname` | `"neglify"` |
| `originalmovietitle` | `"the-matrix"` |
| `fanedittype` | `"fanfix"` |
| `faneditreleasedate` | `"2023"` |
| `award` | `"fanedit-of-the-month"` |

Any tag slug visible in a fanedit.org tag URL will work.

### `iter_by_tag`

`pyfanedit/client.py:171` — paginating generator, same parameters plus `max_pages`.

---

## Category Browsing

### `get_category`

`pyfanedit/client.py:70`

```python
get_category(category: str, page: int = 1) -> tuple[list[FaneditSummary], str | None]
```

`category` is a key from `CATEGORIES` or a raw URL path. Available keys:

```
fanfix  fanmix  extended  tv_to_movie  movie_to_tv
shorts  special  documentary  preservation  unapproved
```

### `iter_category`

`pyfanedit/client.py:85` — paginating generator.

---

## Detail

### `get_detail`

`pyfanedit/client.py:232`

```python
get_detail(url: str) -> FaneditDetail
```

`url` may be a full URL (`https://fanedit.org/…`) or a bare slug (`"star-wars-begins"`).

### `get_detail_by_slug`

`pyfanedit/client.py:244`

```python
get_detail_by_slug(slug: str) -> FaneditDetail
```

Equivalent to `get_detail("https://fanedit.org/{slug}/")`.

---

## Reviewer Leaderboard

### `get_reviewer_rank`

`pyfanedit/client.py:258`

```python
get_reviewer_rank(page: int = 1) -> tuple[list[ReviewerEntry], str | None]
```

~50 entries per page. Each `ReviewerEntry.user_id` is the stable numeric key for `get_user_reviews`.

### `iter_reviewer_rank`

`pyfanedit/client.py:267` — paginating generator.

---

## Reviews by User

### `get_user_reviews`

`pyfanedit/client.py:296`

```python
get_user_reviews(
    user_id: int,
    page: int = 1,
    order: str = "rdate",
) -> tuple[list[UserReviewEntry], str | None]
```

### `iter_user_reviews`

`pyfanedit/client.py:318` — paginating generator.

### `get_latest_user_reviews`

`pyfanedit/client.py:327`

```python
get_latest_user_reviews(page: int = 1) -> tuple[list[FaneditSummary], str | None]
```

Latest-reviews feed across all users.

### `get_latest_trusted_reviews`

`pyfanedit/client.py:332`

```python
get_latest_trusted_reviews(page: int = 1) -> tuple[list[FaneditSummary], str | None]
```

Latest trusted-reviewer reviews feed.

### `REVIEW_ORDER_CHOICES`

`pyfanedit/client.py:281`

| Value | Sort order |
|---|---|
| `rdate` | Most recently written (default) |
| `date` | Oldest first |
| `rating` | Highest overall rating first |
| `rrating` | Lowest overall rating first |
| `updated` | Most recently edited first |
| `helpful` | Most helpful votes first |
| `rhelpful` | Least helpful votes first |
| `discussed` | Most comments first |

---

## News

### `get_news`

`pyfanedit/client.py:341`

```python
get_news() -> list[NewsArticle]
```

Returns up to ~15 article cards from the news front page. `body_html`, `body_text`, `views`, `category`, and `mentioned_fanedit_urls` are always empty — call `get_news_article` to populate them.

### `get_news_article`

`pyfanedit/client.py:347`

```python
get_news_article(url: str) -> NewsArticle
```

Fetches the full article including body text and all IFDB fanedit URLs mentioned. `url` may be a full URL or a forums-relative path.

```python
articles = client.get_news()
full = client.get_news_article(articles[0].url)
for fanedit_url in full.mentioned_fanedit_urls:
    detail = client.get_detail(fanedit_url)
```

---

## See also

- [Models](models.md)
- [Transport and Session Injection](transport.md)
- [mediavocab Converter](converter.md)
