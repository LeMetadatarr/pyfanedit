# API Reference

## FaneditClient

`pyfanedit/client.py:27`

The single entry point for all fanedit.org interactions. Wraps a `Session` internally.

### Constructor

```python
FaneditClient(impersonate: str = "chrome120", cache_ttl: float = 300.0)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `impersonate` | `str` | `"chrome120"` | Browser profile passed to `curl_cffi` for TLS fingerprinting |
| `cache_ttl` | `float` | `300.0` | Seconds before a cached response expires; `0` disables caching |

---

### Category Browsing

#### `get_category`

`pyfanedit/client.py:37`

```python
get_category(category: str, page: int = 1) -> tuple[list[FaneditSummary], str | None]
```

Return one page of a named category.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `category` | `str` | — | A key from `CATEGORIES` (e.g. `"fanfix"`) or a raw URL path |
| `page` | `int` | `1` | 1-based page number |

Returns `(items, next_page_url)` where `next_page_url` is `None` on the last page.

```python
items, next_page = client.get_category("fanfix")
print(items[0].title, next_page)
```

#### `iter_category`

`pyfanedit/client.py:52`

```python
iter_category(category: str, max_pages: int = 0) -> Iterator[FaneditSummary]
```

Yield every fanedit in a category across all pages. Set `max_pages` to a positive integer
to stop early.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `category` | `str` | — | Same as `get_category` |
| `max_pages` | `int` | `0` | Maximum pages to fetch; `0` means unlimited |

```python
for edit in client.iter_category("extended", max_pages=2):
    print(edit.title)
```

---

### Search

#### `search`

`pyfanedit/client.py:67`

```python
search(
    keywords: str,
    scope: str = "title",
    query_type: str = "all",
    order: str = "rdate",
    page: int = 1,
) -> tuple[list[FaneditSummary], str | None]
```

Search the IFDB and return one page of results.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `keywords` | `str` | — | Search terms |
| `scope` | `str` | `"title"` | `"title"` or `"reviews"` |
| `query_type` | `str` | `"all"` | `"all"` (match all words), `"any"` (match any word), `"exact"` (exact phrase) |
| `order` | `str` | `"rdate"` | Sort order — see `ORDER_CHOICES` |
| `page` | `int` | `1` | 1-based page number |

Returns `(items, next_page_url)`.

```python
results, next_page = client.search("batman", order="rvote")
```

#### `iter_search`

`pyfanedit/client.py:98`

```python
iter_search(
    keywords: str,
    scope: str = "title",
    query_type: str = "all",
    order: str = "rdate",
    max_pages: int = 0,
) -> Iterator[FaneditSummary]
```

Yield all search results across pages. Parameters match `search` except `page` is managed
internally. `max_pages=0` means no limit.

```python
for edit in client.iter_search("star trek", query_type="any", max_pages=5):
    print(edit.title, edit.user_rating)
```

---

### Tag / Franchise Browsing

#### `get_by_tag`

`pyfanedit/client.py:120`

```python
get_by_tag(tag_type: str, tag_value: str, page: int = 1) -> tuple[list[FaneditSummary], str | None]
```

Browse by a structured tag. Returns `(items, next_page_url)`.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `tag_type` | `str` | — | Tag dimension (e.g. `"franchise"`, `"faneditorname"`) |
| `tag_value` | `str` | — | Slugified tag value (e.g. `"star-wars"`) |
| `page` | `int` | `1` | 1-based page number |

```python
items, _ = client.get_by_tag("franchise", "star-wars")
```

#### `iter_by_tag`

`pyfanedit/client.py:138`

```python
iter_by_tag(tag_type: str, tag_value: str, max_pages: int = 0) -> Iterator[FaneditSummary]
```

Yield all results for a tag across pages.

---

### Curated Lists

All curated-list methods share the same signature pattern:

```python
method(page: int = 1) -> tuple[list[FaneditSummary], str | None]
```

| Method | URL path | Description |
|---|---|---|
| `get_latest` | `latest-ifdb-fanedits/` | Most recently added edits |
| `get_top_trusted_rated` | `top-trusted-reviewer-rated-fanedits/` | Highest rated by trusted reviewers |
| `get_top_user_rated` | `top-user-rated-fanedits/` | Highest rated by all users |
| `get_most_popular` | `most-popular/` | Most viewed edits |
| `get_award_winners` | tag `award/fanedit-of-the-month` | Fanedit of the Month winners |

`pyfanedit/client.py:153`

```python
items, next_page = client.get_top_user_rated()
```

---

### Detail

#### `get_detail`

`pyfanedit/client.py:176`

```python
get_detail(url: str) -> FaneditDetail
```

Fetch and parse a single fanedit detail page.

| Parameter | Type | Description |
|---|---|---|
| `url` | `str` | Full URL (`https://fanedit.org/…`) or bare slug (`"my-edit-title"`) |

```python
detail = client.get_detail("https://fanedit.org/star-wars-begins/")
# or equivalently:
detail = client.get_detail("star-wars-begins")
print(detail.imdb_id, detail.genre, detail.time_cut)
```

---

## Constants

### `CATEGORIES`

`pyfanedit/client.py:11`

```python
CATEGORIES = {
    "fanfix":        "category/fanedit-listings/fanfix/",
    "fanmix":        "category/fanedit-listings/fanmix/",
    "extended":      "category/fanedit-listings/extended-edition/",
    "tv_to_movie":   "category/fanedit-listings/tv-to-movie/",
    "movie_to_tv":   "category/fanedit-listings/movie-to-tv/",
    "shorts":        "category/fanedit-listings/shorts/",
    "special":       "category/fanedit-listings/custom-special-edition/",
    "documentary":   "category/fanedit-listings/documentary-review/",
    "preservation":  "category/preservation-listings/",
    "unapproved":    "category/unapproved-fanedits/",
}
```

### `ORDER_CHOICES`

`pyfanedit/client.py:24`

```python
ORDER_CHOICES = ("rdate", "date", "modified", "alpha", "rratio", "rvote")
```

| Value | Meaning |
|---|---|
| `rdate` | Fanedit release date, newest first (default) |
| `date` | Date added to IFDB, newest first |
| `modified` | Last modified date, newest first |
| `alpha` | Alphabetical by title |
| `rratio` | Highest editor/trusted-reviewer rating first |
| `rvote` | Most user votes first |

---

## Models

### `FaneditSummary`

`pyfanedit/models.py:28`

Populated from listing pages (category, search, tag, curated lists). Fields that require
the detail page are always `None` here.

| Field | Type | Nullable | Source on page |
|---|---|---|---|
| `fanedit_id` | `int` | Yes — always `None` on summary | WordPress `postid-NNN` body class (detail page only) |
| `slug` | `str` | Yes | Derived from URL path (`_slug_from_url`) |
| `title` | `str` | No | `.jrListingTitle a` text |
| `url` | `str` | No | `.jrListingTitle a` href |
| `cover_url` | `str` | Yes | `.jrListingThumbnail img` `data-jr-src` or `src` |
| `faneditor` | `str` | Yes | `jrFieldRow` with label `"faneditor name:"` |
| `original_title` | `str` | Yes | `jrFieldRow` with label `"original movie/show title:"` |
| `fanedit_type` | `str` | Yes | `jrFieldRow` label `"fanedit type:"` or `.jrListingCategory` |
| `franchise` | `str` | Yes | `jrFieldRow` with label `"franchise:"` (plain text on summary) |
| `release_date` | `str` | Yes | `jrFieldRow` with label `"fanedit release date:"` |
| `running_time` | `str` | Yes | `jrFieldRow` with label `"fanedit running time:"` |
| `synopsis` | `str` | Yes | `jrFieldRow` with label `"synopsis:"` |
| `editor_rating` | `float` | Yes | `.jrOverallEditor .jrRatingValue` |
| `user_rating` | `float` | Yes | `.jrOverallUser .jrRatingValue` |
| `user_rating_count` | `int` | Yes | Vote count in parentheses next to user rating |
| `views` | `int` | Yes | Span containing `.jrIconGraph` icon |
| `updated` | `str` | Yes | `.jrDateValue` |

---

### `FaneditDetail`

`pyfanedit/models.py:51`

Populated from a single fanedit detail page. Contains all `FaneditSummary` fields (with
the same-named counterparts) plus the additional fields below.

| Field | Type | Nullable | Source on page |
|---|---|---|---|
| `fanedit_id` | `int` | Yes | `postid-NNN` CSS class on `<body>` |
| `slug` | `str` | Yes | Derived from URL |
| `title` | `str` | No | `.jrListingTitle` or `<h1>` text |
| `url` | `str` | No | URL passed to `get_detail` |
| `cover_url` | `str` | Yes | `.jrMediaPhoto` `data-jr-src` or `src` |
| `faneditor` | `str` | Yes | `jrFieldRow` label `"faneditor name:"` |
| `original_title` | `str` | Yes | `jrFieldRow` label `"original movie/show title:"` |
| `genre` | `list[str]` | Yes | `jrFieldRow` label `"genre:"` — list of linked tags |
| `franchise` | `list[str]` | Yes | `jrFieldRow` label `"franchise:"` — list of linked tags |
| `fanedit_type` | `str` | Yes | `jrFieldRow` label `"fanedit type:"` |
| `imdb_id` | `str` | Yes | First `/(tt\d+)` match in any `<a href>` on the page |
| `original_release_date` | `str` | Yes | `jrFieldRow` label `"original release date:"` |
| `original_running_time` | `str` | Yes | `jrFieldRow` label `"original running time:"` |
| `fanedit_release_date` | `str` | Yes | `jrFieldRow` label `"fanedit release date:"` |
| `fanedit_running_time` | `str` | Yes | `jrFieldRow` label `"fanedit running time:"` |
| `time_cut` | `str` | Yes | `jrFieldRow` label `"time cut:"` |
| `time_added` | `str` | Yes | `jrFieldRow` label `"time added:"` |
| `subtitles` | `str` | Yes | `jrFieldRow` label `"subtitles available:"` |
| `available_in` | `str` | Yes | `jrFieldRow` label `"available in:"` |
| `release_information` | `str` | Yes | `jrFieldRow` label `"release information:"` |
| `synopsis` | `str` | Yes | `jrFieldRow` label `"synopsis:"` |
| `additional_notes` | `str` | Yes | `jrFieldRow` label `"additional notes:"` |
| `special_thanks` | `str` | Yes | `jrFieldRow` label `"special thanks:"` |
| `cuts_and_additions` | `str` | Yes | `jrFieldRow` label `"cuts and additions:"` |
| `intention` | `str` | Yes | `jrFieldRow` label `"intention:"` |
| `awards` | `str` | Yes | `jrFieldRow` label `"awards:"` |
| `editor_rating` | `float` | Yes | `.jrOverallEditor .jrRatingValue` |
| `user_rating` | `float` | Yes | `.jrOverallUser .jrRatingValue` |
| `user_rating_count` | `int` | Yes | Vote count next to user rating |
| `editor_reviews` | `list[Review]` | No (empty list) | `.jrEditorReviewsContainer` |
| `user_reviews` | `list[Review]` | No (empty list) | `.jrUserReviewsContainer` |
| `extra_fields` | `dict[str, str]` | No (empty dict) | Any `jrFieldRow` whose label is not in the known map |

---

### `Review`

`pyfanedit/models.py:15`

| Field | Type | Nullable | Source |
|---|---|---|---|
| `reviewer` | `str` | Yes | `[itemprop="name"]` in `.jrReviewLayoutLeft` |
| `reviewer_url` | `str` | Yes | `[itemprop="url"]` href |
| `reviewer_rank` | `str` | Yes | `.jrReviewerRank` text |
| `reviewer_review_count` | `int` | Yes | First number in `.jrReviewerReviews` text |
| `date` | `str` | Yes | `time.jrReviewCreated` `datetime` attribute or text |
| `ratings` | `ReviewRatings` | No (empty model) | `.jrRatingTable` |
| `body` | `str` | Yes | `.jrReviewComment` text |
| `discussion_url` | `str` | Yes | `.jrDiscussReview` href |
| `helpful_yes` | `int` | Yes | `.jrVoteYes .count-text` |
| `helpful_no` | `int` | Yes | `.jrVoteNo .count-text` |

---

### `ReviewRatings`

`pyfanedit/models.py:6`

All fields are `Optional[float]`, defaulting to `None` if the rating row is absent.

| Field | Label on page |
|---|---|
| `overall` | `"overall rating"` |
| `audio_video_quality` | `"audio/video quality"` |
| `audio_editing` | `"audio editing"` |
| `visual_editing` | `"visual editing"` |
| `narrative` | `"narrative"` |
| `enjoyment` | `"enjoyment"` |

---

## See also

- [Quick Start](quickstart.md)
- [IDs, IMDB Mapping, and Metadata](ids-and-metadata.md)
- [Advanced Usage](advanced.md)
