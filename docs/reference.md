# API Reference

## FaneditClient

`pyfanedit/client.py:27`

The single entry point for all fanedit.org interactions. It wraps a `Session` internally.

### Constructor

```python
FaneditClient(impersonate: str = "chrome120", cache_ttl: float = 300.0)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `impersonate` | `str` | `"chrome120"` | Browser profile passed to `curl_cffi` for TLS fingerprinting |
| `cache_ttl` | `float` | `300.0` | Seconds before a cached response expires. `0` disables caching |

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
| `category` | `str` | - | A key from `CATEGORIES` (e.g. `"fanfix"`) or a raw URL path |
| `page` | `int` | `1` | 1-based page number |

Returns `(items, next_page_url)`. `next_page_url` is `None` on the last page.

```python
items, next_page = client.get_category("fanfix")
print(items[0].title, next_page)
```

#### `iter_category`

`pyfanedit/client.py:52`

```python
iter_category(category: str, max_pages: int = 0) -> Iterator[FaneditSummary]
```

Yield every fanedit in a category across all pages. Set `max_pages` to a positive integer to stop early.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `category` | `str` | - | Same as `get_category` |
| `max_pages` | `int` | `0` | Maximum pages to fetch. `0` means unlimited |

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
| `keywords` | `str` | - | Search terms |
| `scope` | `str` | `"title"` | `"title"` or `"reviews"` |
| `query_type` | `str` | `"all"` | `"all"` (match all words), `"any"` (match any word), `"exact"` (exact phrase) |
| `order` | `str` | `"rdate"` | Sort order - see `ORDER_CHOICES` |
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

Yield all search results across pages. Parameters match `search`, except `page` is managed internally. `max_pages=0` means no limit.

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
| `tag_type` | `str` | - | Tag dimension (e.g. `"franchise"`, `"faneditorname"`) |
| `tag_value` | `str` | - | Slugified tag value (e.g. `"star-wars"`) |
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

### Reviewer Leaderboard

#### `get_reviewer_rank`

`pyfanedit/client.py:190`

```python
get_reviewer_rank(page: int = 1) -> tuple[list[ReviewerEntry], str | None]
```

Return one page of the reviewer leaderboard (about 50 entries per page).

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | `int` | `1` | 1-based page number |

Returns `(entries, next_page_url)`. `next_page_url` is `None` on the last page. Each `ReviewerEntry` includes a `user_id` that you can pass directly to `get_user_reviews`.

```python
entries, _ = client.get_reviewer_rank()
print(entries[0].username, entries[0].review_count, entries[0].helpful_pct)
```

#### `iter_reviewer_rank`

`pyfanedit/client.py:199`

```python
iter_reviewer_rank(max_pages: int = 0) -> Iterator[ReviewerEntry]
```

Yield all reviewers from the leaderboard across pages. `max_pages=0` means no limit.

```python
for reviewer in client.iter_reviewer_rank(max_pages=2):
    print(reviewer.rank, reviewer.username)
```

---

### Reviews by User

#### `get_user_reviews`

`pyfanedit/client.py:224`

```python
get_user_reviews(
    user_id: int,
    page: int = 1,
    order: str = "rdate",
) -> tuple[list[UserReviewEntry], str | None]
```

Return one page of reviews written by a specific user.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `user_id` | `int` | - | Numeric jReviews user ID from `ReviewerEntry.user_id` |
| `page` | `int` | `1` | 1-based page number |
| `order` | `str` | `"rdate"` | Sort order - see `REVIEW_ORDER_CHOICES` |

Returns `(reviews, next_page_url)`.

```python
reviews, _ = client.get_user_reviews(1234, order="helpful")
for r in reviews:
    print(r.fanedit_title, r.ratings.overall)
```

#### `iter_user_reviews`

`pyfanedit/client.py:244`

```python
iter_user_reviews(
    user_id: int,
    order: str = "rdate",
    max_pages: int = 0,
) -> Iterator[UserReviewEntry]
```

Yield all reviews written by a user across pages.

```python
for review in client.iter_user_reviews(1234, max_pages=5):
    print(review.date, review.fanedit_title)
```

#### `get_latest_user_reviews`

`pyfanedit/client.py:259`

```python
get_latest_user_reviews(page: int = 1) -> tuple[list[FaneditSummary], str | None]
```

Return the latest-user-reviews feed (all users). Returns `(items, next_page_url)`.

```python
items, _ = client.get_latest_user_reviews()
```

#### `get_latest_trusted_reviews`

`pyfanedit/client.py:264`

```python
get_latest_trusted_reviews(page: int = 1) -> tuple[list[FaneditSummary], str | None]
```

Return the latest trusted-reviewer reviews feed. Returns `(items, next_page_url)`.

```python
items, _ = client.get_latest_trusted_reviews()
```

---

### News

#### `get_news`

`pyfanedit/client.py:273`

```python
get_news() -> list[NewsArticle]
```

Return the news front-page article cards (about 15 articles at most). Card-level fields are populated. `body_html`, `body_text`, `views`, `category`, and `mentioned_fanedit_urls` are always empty - call `get_news_article` for those.

```python
articles = client.get_news()
for a in articles:
    print(a.title, a.published_at)
```

#### `get_news_article`

`pyfanedit/client.py:278`

```python
get_news_article(url: str) -> NewsArticle
```

Fetch a full news article, including body text and IFDB URLs mentioned in the body.

| Parameter | Type | Description |
|---|---|---|
| `url` | `str` | Full URL or a forums-relative path such as `"/forums/news-publisher/some-article.185/"` |

```python
article = client.get_news_article("https://fanedit.org/forums/news-publisher/some-article.185/")
print(article.body_text)
for fanedit_url in article.mentioned_fanedit_urls:
    detail = client.get_detail(fanedit_url)
    print(detail.title)
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

### `REVIEW_ORDER_CHOICES`

`pyfanedit/client.py:213`

Controls the sort order for `get_user_reviews` and `iter_user_reviews`.

```python
REVIEW_ORDER_CHOICES = (
    "rdate",     # most recent
    "date",      # oldest first
    "rating",    # highest overall rating first
    "rrating",   # lowest overall rating first (most critical)
    "updated",   # last updated first
    "helpful",   # most helpful votes first
    "rhelpful",  # least helpful votes first
    "discussed", # most comments first
)
```

| Value | Sort order |
|---|---|
| `rdate` | Most recently written, newest first (default) |
| `date` | Oldest reviews first |
| `rating` | Highest overall rating first |
| `rrating` | Lowest overall rating first |
| `updated` | Most recently edited first |
| `helpful` | Most helpful votes first |
| `rhelpful` | Least helpful votes first |
| `discussed` | Most comments first |

---

## Models

### `FaneditSummary`

`pyfanedit/models.py:28`

Populated from listing pages (category, search, tag, curated lists). Fields that need the detail page are always `None` here.

| Field | Type | Nullable | Source on page |
|---|---|---|---|
| `fanedit_id` | `int` | Yes - always `None` on summary | WordPress `postid-NNN` body class (detail page only) |
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

Populated from a single fanedit detail page. Contains all `FaneditSummary` fields (with the same-named counterparts) plus the additional fields below.

| Field | Type | Nullable | Source on page |
|---|---|---|---|
| `fanedit_id` | `int` | Yes | `postid-NNN` CSS class on `<body>` |
| `slug` | `str` | Yes | Derived from URL |
| `title` | `str` | No | `.jrListingTitle` or `<h1>` text |
| `url` | `str` | No | URL passed to `get_detail` |
| `cover_url` | `str` | Yes | `.jrMediaPhoto` `data-jr-src` or `src` |
| `faneditor` | `str` | Yes | `jrFieldRow` label `"faneditor name:"` |
| `original_title` | `str` | Yes | `jrFieldRow` label `"original movie/show title:"` |
| `genre` | `list[str]` | Yes | `jrFieldRow` label `"genre:"` - list of linked tags |
| `franchise` | `list[str]` | Yes | `jrFieldRow` label `"franchise:"` - list of linked tags |
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

All fields are `Optional[float]`, and default to `None` if the rating row is absent.

| Field | Label on page |
|---|---|
| `overall` | `"overall rating"` |
| `audio_video_quality` | `"audio/video quality"` |
| `audio_editing` | `"audio editing"` |
| `visual_editing` | `"visual editing"` |
| `narrative` | `"narrative"` |
| `enjoyment` | `"enjoyment"` |

---

### `ReviewerEntry`

`pyfanedit/models.py:101`

One row from the reviewer leaderboard (`/reviewer-rank/`). The `user_id` field is the stable numeric key used by `get_user_reviews`.

| Field | Type | Nullable | Source |
|---|---|---|---|
| `rank` | `int` | No | Rank number in the leaderboard column |
| `user_id` | `int` | No | `id="user-N"` on the rank column element |
| `username` | `str` | No | `.jrReviewAuthor a` text |
| `profile_url` | `str` | No | `.jrReviewAuthor a` href |
| `reviews_url` | `str` | No | Review count link href, or constructed as `/my-reviews/{user_id}/` |
| `review_count` | `int` | No | Number in the review count link text |
| `helpful_yes` | `int` | Yes | First number in `"Helpful votes: N (P%)"` |
| `helpful_pct` | `float` | Yes | Percentage in `"Helpful votes: N (P%)"` |

---

### `UserReviewEntry`

`pyfanedit/models.py:113`

One review from a user's review list page (`/my-reviews/{user_id}/`). Contains the fanedit being reviewed and the ratings given, but not the review body text (that text is only available on the fanedit detail page).

| Field | Type | Nullable | Source |
|---|---|---|---|
| `fanedit_title` | `str` | No | `.jrListingTitle a` text |
| `fanedit_url` | `str` | No | `.jrListingTitle a` href, always absolute |
| `fanedit_type` | `str` | Yes | `.jrListingCategory` text |
| `date` | `str` | Yes | `.jrReviewCreated` `datetime` attribute or text |
| `ratings` | `ReviewRatings` | No (empty model) | `.jrRatingTable` |
| `discussion_url` | `str` | Yes | `href` of the comments button containing `/discussions/` |
| `comment_count` | `int` | Yes | Number in `"Comments (N)"` button text |

---

### `NewsArticle`

`pyfanedit/models.py:124`

A news article. Fields from the listing card are always populated when `get_news` returns them. Fields marked "article page only" are `None` from `get_news`, and are populated only when you fetch a specific article with `get_news_article`.

| Field | Type | Nullable | Source |
|---|---|---|---|
| `thread_id` | `int` | No | `js-threadListItem-N` CSS class on the card element |
| `title` | `str` | No | `.newsCard-grid-title a` text (card) or `h1.p-title-value` (article) |
| `url` | `str` | No | Card link href or URL passed to `get_news_article` |
| `thumbnail_url` | `str` | Yes | `img.newsCard-grid-image-link` `src` (card) or `img.newsView-newsThumbnail-header` `src` (article) |
| `author` | `str` | Yes | `img[alt]` inside the avatar link (card) or `a[data-user-id]` text (article) |
| `author_user_id` | `int` | Yes | `data-user-id` attribute on the avatar link |
| `published_at` | `str` | Yes | `time` element `datetime` attribute (ISO string) |
| `reading_time` | `str` | Yes | `li.newsCard-date` text containing `"min read"` |
| `views` | `int` | Yes | Article page only - `"Views N"` in `.pairs--justified` |
| `category` | `str` | Yes | Article page only - last breadcrumb link text |
| `body_html` | `str` | Yes | Article page only - raw HTML of `.bbWrapper` |
| `body_text` | `str` | Yes | Article page only - plain text of `.bbWrapper` |
| `mentioned_fanedit_urls` | `list[str]` | No (empty list) | Article page only - all `<a href>` inside `.bbWrapper` pointing to `fanedit.org` but not to `/forums/` |

---
[← Quick Start](quickstart.md) · [Home](index.md) · [IDs, IMDB Mapping, and Metadata →](ids-and-metadata.md)
