# Models

All models are Pydantic v2 `BaseModel` subclasses. Use `model_dump()` / `model_dump_json()` for serialisation.

---

## `FaneditSummary`

`pyfanedit/models.py:28`

Returned from listing, search, tag, and curated-list pages. Fields that require the detail page are always `None` here.

| Field | Type | Source on page |
|---|---|---|
| `fanedit_id` | `int \| None` | Always `None` — `postid-NNN` only on detail pages |
| `slug` | `str \| None` | Derived from URL path |
| `title` | `str` | `.jrListingTitle a` text |
| `url` | `str` | `.jrListingTitle a` href |
| `cover_url` | `str \| None` | `data-jr-src` or `src` on thumbnail img |
| `faneditor` | `str \| None` | Field row `"faneditor name:"` |
| `original_title` | `str \| None` | Field row `"original movie/show title:"` |
| `fanedit_type` | `str \| None` | Field row `"fanedit type:"` or `.jrListingCategory` |
| `franchise` | `str \| None` | Field row `"franchise:"` (plain text string on summary) |
| `release_date` | `str \| None` | Field row `"fanedit release date:"` |
| `running_time` | `str \| None` | Field row `"fanedit running time:"` |
| `synopsis` | `str \| None` | Field row `"synopsis:"` |
| `editor_rating` | `float \| None` | `.jrOverallEditor .jrRatingValue` |
| `user_rating` | `float \| None` | `.jrOverallUser .jrRatingValue` |
| `user_rating_count` | `int \| None` | Vote count next to user rating |
| `views` | `int \| None` | Span containing `.jrIconGraph` icon |
| `updated` | `str \| None` | `.jrDateValue` |

---

## `FaneditDetail`

`pyfanedit/models.py:51`

Returned from `get_detail` / `get_detail_by_slug`. Contains all `FaneditSummary` fields (renamed where the detail page has richer variants) plus:

| Field | Type | Source on page |
|---|---|---|
| `fanedit_id` | `int \| None` | `postid-NNN` CSS class on `<body>` |
| `genre` | `list[str] \| None` | Field row `"genre:"` — list of linked tags |
| `franchise` | `list[str] \| None` | Field row `"franchise:"` — list of linked tags |
| `imdb_id` | `str \| None` | First `/(tt\d+)` match in any `<a href>` on the page |
| `original_release_date` | `str \| None` | Field row `"original release date:"` |
| `original_running_time` | `str \| None` | Field row `"original running time:"` |
| `fanedit_release_date` | `str \| None` | Field row `"fanedit release date:"` |
| `fanedit_running_time` | `str \| None` | Field row `"fanedit running time:"` |
| `time_cut` | `str \| None` | Field row `"time cut:"` |
| `time_added` | `str \| None` | Field row `"time added:"` |
| `subtitles` | `str \| None` | Field row `"subtitles available:"` |
| `available_in` | `str \| None` | Field row `"available in:"` |
| `release_information` | `str \| None` | Field row `"release information:"` |
| `additional_notes` | `str \| None` | Field row `"additional notes:"` |
| `special_thanks` | `str \| None` | Field row `"special thanks:"` |
| `cuts_and_additions` | `str \| None` | Field row `"cuts and additions:"` |
| `intention` | `str \| None` | Field row `"intention:"` |
| `awards` | `str \| None` | Field row `"awards:"` |
| `editor_reviews` | `list[Review]` | `.jrEditorReviewsContainer` |
| `user_reviews` | `list[Review]` | `.jrUserReviewsContainer` |
| `extra_fields` | `dict[str, str]` | Any field row whose label is not in `_DETAIL_FIELD_MAP` |

`franchise` is `list[str]` on `FaneditDetail` but `str | None` on `FaneditSummary`. Code that handles both models must branch on type.

`extra_fields` is a safety net: new metadata labels added by fanedit.org land here rather than being silently dropped. — `pyfanedit/parsers.py:12`

---

## `Review`

`pyfanedit/models.py:15`

Embedded in `FaneditDetail.editor_reviews` and `FaneditDetail.user_reviews`.

| Field | Type | Source |
|---|---|---|
| `reviewer` | `str \| None` | `[itemprop="name"]` in `.jrReviewLayoutLeft` |
| `reviewer_url` | `str \| None` | `[itemprop="url"]` href |
| `reviewer_rank` | `str \| None` | `.jrReviewerRank` text |
| `reviewer_review_count` | `int \| None` | First number in `.jrReviewerReviews` text |
| `date` | `str \| None` | `time.jrReviewCreated` `datetime` attribute or text |
| `ratings` | `ReviewRatings` | `.jrRatingTable` |
| `body` | `str \| None` | `.jrReviewComment` text |
| `discussion_url` | `str \| None` | `.jrDiscussReview` href |
| `helpful_yes` | `int \| None` | `.jrVoteYes .count-text` |
| `helpful_no` | `int \| None` | `.jrVoteNo .count-text` |

---

## `ReviewRatings`

`pyfanedit/models.py:6`

All fields are `Optional[float]`, defaulting to `None` when the rating row is absent.

| Field | Label on page |
|---|---|
| `overall` | `"overall rating"` |
| `audio_video_quality` | `"audio/video quality"` |
| `audio_editing` | `"audio editing"` |
| `visual_editing` | `"visual editing"` |
| `narrative` | `"narrative"` |
| `enjoyment` | `"enjoyment"` |

---

## `ReviewerEntry`

`pyfanedit/models.py:101`

One row from the reviewer leaderboard (`/reviewer-rank/`).

| Field | Type | Source |
|---|---|---|
| `rank` | `int` | Rank column number |
| `user_id` | `int` | `id="user-N"` on the rank column element — pass directly to `get_user_reviews` |
| `username` | `str` | `.jrReviewAuthor a` text |
| `profile_url` | `str` | `.jrReviewAuthor a` href |
| `reviews_url` | `str` | Review-count link href, or `/my-reviews/{user_id}/` |
| `review_count` | `int` | Number in the review count link text |
| `helpful_yes` | `int \| None` | First number in `"Helpful votes: N (P%)"` |
| `helpful_pct` | `float \| None` | Percentage in `"Helpful votes: N (P%)"` |

---

## `UserReviewEntry`

`pyfanedit/models.py:113`

One review from a user's review list page (`/my-reviews/{user_id}/`). Does not include review body text — that is only on the fanedit detail page.

| Field | Type | Source |
|---|---|---|
| `fanedit_title` | `str` | `.jrListingTitle a` text |
| `fanedit_url` | `str` | `.jrListingTitle a` href (always absolute) |
| `fanedit_type` | `str \| None` | `.jrListingCategory` text |
| `date` | `str \| None` | `.jrReviewCreated` `datetime` attribute or text |
| `ratings` | `ReviewRatings` | `.jrRatingTable` |
| `discussion_url` | `str \| None` | href of the comments button |
| `comment_count` | `int \| None` | Number in `"Comments (N)"` button text |

---

## `NewsArticle`

`pyfanedit/models.py:124`

Fields populated from the listing card are always present when returned by `get_news`. Fields marked "article page only" are `None` from `get_news` and populated only by `get_news_article`.

| Field | Type | Notes |
|---|---|---|
| `thread_id` | `int` | `js-threadListItem-N` CSS class on card |
| `title` | `str` | Card link or article `<h1>` |
| `url` | `str` | Card href or URL passed to `get_news_article` |
| `thumbnail_url` | `str \| None` | Card or article header image `src` |
| `author` | `str \| None` | Avatar alt text (card) or `a[data-user-id]` text (article) |
| `author_user_id` | `int \| None` | `data-user-id` attribute |
| `published_at` | `str \| None` | `time` element `datetime` attribute (ISO string) |
| `reading_time` | `str \| None` | Card `li` text containing `"min read"` |
| `views` | `int \| None` | Article page only |
| `category` | `str \| None` | Article page only — last breadcrumb link |
| `body_html` | `str \| None` | Article page only — raw HTML of `.bbWrapper` |
| `body_text` | `str \| None` | Article page only — plain text of `.bbWrapper` |
| `mentioned_fanedit_urls` | `list[str]` | Article page only — all `<a href>` in body pointing to fanedit.org (not `/forums/`) |

---

## See also

- [FaneditClient Reference](reference.md)
- [IDs and Metadata](ids-and-metadata.md)
