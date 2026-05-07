# pyfanedit

Python scraping client for [fanedit.org](https://fanedit.org) (IFDB — the Internet Fanedit Database).

## Overview

fanedit.org hosts a community-curated catalogue of fan-edited films and TV shows. The site has no public API; pyfanedit scrapes HTML with `curl_cffi` (TLS fingerprint bypass) and `BeautifulSoup`, returning typed Pydantic models.

## Key Classes

| Class | Purpose | Source |
|---|---|---|
| `FaneditClient` | All user-facing methods | `pyfanedit/client.py:34` |
| `FaneditSummary` | Lightweight record from listing/search pages | `pyfanedit/models.py:28` |
| `FaneditDetail` | Full record from a single fanedit detail page | `pyfanedit/models.py:51` |
| `Review` | One editor or user review embedded in a detail page | `pyfanedit/models.py:15` |
| `ReviewRatings` | Per-dimension ratings inside a review | `pyfanedit/models.py:6` |
| `ReviewerEntry` | One row from the reviewer leaderboard | `pyfanedit/models.py:101` |
| `UserReviewEntry` | One review from a user's review list page | `pyfanedit/models.py:113` |
| `NewsArticle` | News article card or full article body | `pyfanedit/models.py:124` |
| `Session` | HTTP layer: caching, TLS impersonation | `pyfanedit/session.py:74` |

## Contents

- [Getting Started](getting-started.md) — install, first search, pagination, pitfalls
- [FaneditClient Reference](reference.md) — all 16 methods grouped by function
- [Models](models.md) — every model field with source annotations
- [Transport and Session Injection](transport.md) — curl_cffi, PYFANEDIT_TRANSPORT, custom sessions
- [mediavocab Converter](converter.md) — `fanedit_to_release` shape and field mapping
- [IDs and Metadata](ids-and-metadata.md) — slug / fanedit_id / imdb_id availability matrix
