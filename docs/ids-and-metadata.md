# IDs, IMDB Mapping, and Metadata Guide

## The Three Identifier Types

Every fanedit on IFDB can be referenced by up to three different identifiers.

### `slug`

The URL slug is the last path segment of a fanedit's canonical URL, for example
`"star-wars-begins"` from `https://fanedit.org/star-wars-begins/`.

- Always available on both listing and detail pages.
- Derived by `_slug_from_url` — `pyfanedit/parsers.py:95`.
- Human-readable but not guaranteed unique across all time (a slug could theoretically
  be reused if an entry is deleted).
- Use the slug when constructing a URL to pass to `get_detail`.

### `fanedit_id`

The WordPress post ID, an integer such as `12345`.

- **Only available on detail pages.** On listing/search pages it is always `None`.
- Extracted from the `postid-NNN` CSS class on the `<body>` element — `pyfanedit/parsers.py:85`.
- Stable across slug changes.
- Use this as a persistent primary key when building a local dataset.

### `imdb_id`

An IMDB title identifier in the form `tt0076759`.

- **Only available on detail pages.**
- Extracted by scanning all `<a href>` elements for the pattern `/(tt\d+)` — `pyfanedit/parsers.py:77`.
- Not guaranteed: some edits have no IMDB link; others have a malformed URL where the
  IMDB link is nested inside a fanedit.org URL (e.g.
  `https://fanedit.org/https://imdb.com/title/tt0076759/`). The regex still finds the
  `tt` ID in that case, but verify before relying on it.
- Links to the *source* film/show, not to the fanedit itself (fanedits are not on IMDB).

---

## ID Availability by Page Type

| Identifier | `FaneditSummary` (listing/search) | `FaneditDetail` (detail page) |
|---|---|---|
| `slug` | Yes | Yes |
| `fanedit_id` | No — always `None` | Yes — from `<body class="postid-NNN">` |
| `imdb_id` | No — field does not exist on this model | Yes — may still be `None` if absent |

---

## How to Map a Fanedit to IMDB

1. Obtain a `FaneditSummary` from any listing or search call.
2. Call `client.get_detail(summary.url)` to fetch the detail page.
3. Read `detail.imdb_id`.

```python
from pyfanedit import FaneditClient

client = FaneditClient()
results, _ = client.search("blade runner")
detail = client.get_detail(results[0].url)

if detail.imdb_id:
    imdb_url = f"https://www.imdb.com/title/{detail.imdb_id}/"
    print(f"IMDB: {imdb_url}")
else:
    print("No IMDB link on this page")
```

Always guard against `None`. There is no fallback — if the editor did not link to IMDB,
no `imdb_id` can be inferred.

---

## Full Metadata Field Table

### Fields on `FaneditSummary`

These fields come from the quick-view card shown on listing, search, and tag pages.
Not all fields are present on every card — absent fields default to `None`.

| Field | Type | Notes |
|---|---|---|
| `fanedit_id` | `int \| None` | Always `None` — only available on detail pages |
| `slug` | `str \| None` | Derived from URL |
| `title` | `str` | Always present |
| `url` | `str` | Always present |
| `cover_url` | `str \| None` | `None` if image is lazy-placeholder |
| `faneditor` | `str \| None` | From `"faneditor name:"` field row |
| `original_title` | `str \| None` | From `"original movie/show title:"` field row |
| `fanedit_type` | `str \| None` | From field row or `.jrListingCategory` element |
| `franchise` | `str \| None` | Plain text string on summary (list of strings on detail) |
| `release_date` | `str \| None` | Fanedit release date |
| `running_time` | `str \| None` | Fanedit running time |
| `synopsis` | `str \| None` | Short synopsis text |
| `editor_rating` | `float \| None` | |
| `user_rating` | `float \| None` | |
| `user_rating_count` | `int \| None` | Number of user votes |
| `views` | `int \| None` | Page view count |
| `updated` | `str \| None` | Date string from `.jrDateValue` |

### Fields on `FaneditDetail` (additional, beyond summary)

| Field | Type | Notes |
|---|---|---|
| `imdb_id` | `str \| None` | e.g. `"tt0076759"` |
| `genre` | `list[str] \| None` | List of genre tags |
| `franchise` | `list[str] \| None` | List of franchise tags (contrast: plain string on summary) |
| `original_release_date` | `str \| None` | Source film release year/date |
| `original_running_time` | `str \| None` | Source film runtime |
| `fanedit_release_date` | `str \| None` | |
| `fanedit_running_time` | `str \| None` | |
| `time_cut` | `str \| None` | Total duration removed |
| `time_added` | `str \| None` | Total duration added |
| `subtitles` | `str \| None` | Languages or `"none"` |
| `available_in` | `str \| None` | e.g. `"HD"`, `"Surround Sound"` |
| `release_information` | `str \| None` | e.g. `"Digital"`, `"Physical"` |
| `additional_notes` | `str \| None` | |
| `special_thanks` | `str \| None` | |
| `cuts_and_additions` | `str \| None` | Numbered list of changes, as a single string |
| `intention` | `str \| None` | Editor's stated goal |
| `awards` | `str \| None` | e.g. `"Fanedit of the Month"` |
| `editor_reviews` | `list[Review]` | Empty list if none |
| `user_reviews` | `list[Review]` | Empty list if none |
| `extra_fields` | `dict[str, str]` | Any field row whose label is not in the known map |

---

## Field Availability Matrix

| Field | Listing page | Search page | Tag page | Detail page |
|---|---|---|---|---|
| `slug` | Yes | Yes | Yes | Yes |
| `fanedit_id` | No | No | No | Yes |
| `title` | Yes | Yes | Yes | Yes |
| `url` | Yes | Yes | Yes | Yes |
| `cover_url` | Yes | Yes | Yes | Yes |
| `faneditor` | Yes | Yes | Yes | Yes |
| `original_title` | Yes | Yes | Yes | Yes |
| `fanedit_type` | Yes | Yes | Yes | Yes |
| `franchise` (str) | Partial | Partial | Partial | — |
| `franchise` (list) | — | — | — | Yes |
| `genre` | — | — | — | Yes |
| `imdb_id` | — | — | — | Yes |
| `release_date` / `fanedit_release_date` | Yes | Yes | Yes | Yes |
| `running_time` / `fanedit_running_time` | Yes | Yes | Yes | Yes |
| `synopsis` | Yes | Yes | Yes | Yes |
| `editor_rating` | Yes | Yes | Yes | Yes |
| `user_rating` | Yes | Yes | Yes | Yes |
| `user_rating_count` | Yes | Yes | Yes | Yes |
| `views` | Yes | Yes | Yes | Yes |
| `updated` | Yes | Yes | Yes | — |
| `time_cut` / `time_added` | — | — | — | Yes |
| `subtitles` / `available_in` | — | — | — | Yes |
| `intention` / `cuts_and_additions` | — | — | — | Yes |
| `awards` | — | — | — | Yes |
| `editor_reviews` / `user_reviews` | — | — | — | Yes |

---

## Notable Quirks

**`franchise` type changes between models.** On `FaneditSummary`, `franchise` is an
`Optional[str]` — the raw text of the field row. On `FaneditDetail`, it is
`Optional[list[str]]` — a list of linked tag anchors extracted individually.
Code that handles both must branch on model type.

**`genre` is always a list.** Even if there is a single genre, `FaneditDetail.genre` is
`list[str]`. An empty list is never used — the field is set to `None` when absent.

**Malformed IMDB URLs.** Some pages embed the IMDB link as
`https://fanedit.org/https://www.imdb.com/title/tt0076759/`. The regex in `_imdb_id`
(`/(tt\d+)`) matches in either case, but the double-URL form means the surrounding
`<a>` href cannot be used as-is to open IMDB.

**`extra_fields` as a safety net.** If fanedit.org adds a new metadata label that is not
in `_DETAIL_FIELD_MAP` (`pyfanedit/parsers.py:12`), the value lands in
`FaneditDetail.extra_fields` rather than being silently dropped. Inspect this dict when
debugging missing data.

---

## mediavocab mapping (`fanedit_to_release`)

`pyfanedit.fanedit_to_release()` converts a `FaneditSummary` or
`FaneditDetail` to a typed `mediavocab.Release`. Mapping summary:

| pyfanedit field           | mediavocab destination                                     |
|---------------------------|------------------------------------------------------------|
| `title`                   | `Release.work.title`                                       |
| `cover_url`               | `Release.image`                                            |
| `url`                     | `Release.uri`                                              |
| `faneditor`               | `Release.work.credits[0]` (`role="editor"`, `RelationRole.CREATOR`) |
| `fanedit_type`            | `Release.work.variant_kind` (+ `extra["fanedit_subtype"]`) |
| `fanedit_id`              | `Release.work.external_ids["fanedit_id"]`                  |
| `slug`                    | `Release.work.external_ids["fanedit_slug"]`                |
| `imdb_id` (detail)        | `Release.work.external_ids["derived_from_imdb"]`           |
| `imdb_id` (detail)        | `Work.extra["work_relations"]` → `WorkRelation(kind=FANEDIT_OF, target=<source Work>)` |
| `release_date` / `fanedit_release_date` | `Release.release_date` (ISO 8601), `Work.year` |
| `franchise`, `genre`, `intention`, `synopsis`, `editor_rating`, `user_rating` | `Work.extra` |

Notes:

- The fanedit `Work` itself never holds an IMDb id under `external_ids["imdb"]`
  — fanedits don't have IMDb listings. The source film's id lives in
  `derived_from_imdb` per mediavocab convention.
- `MediaType.MOVIE` for every variant *except* `MOVIE_TO_TV`, which produces
  `MediaType.EPISODIC_SERIES` per the "one Work, one MediaType" axiom.
- Trailers / behind-the-scenes are routed to `MediaType.GENERIC` upstream;
  fanedits stay `MediaType.MOVIE`.
- `PlaybackModality.VIDEO` is recorded on `Work.extra["modality"]`. The
  metadatarr pyfanedit provider declares `modality = {PlaybackModality.VIDEO}`.

---

## See also

- [API Reference](reference.md)
- [Advanced Usage](advanced.md)
- [Quick Start](quickstart.md)
