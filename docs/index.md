# pyfanedit

Python scraping client for [fanedit.org](https://fanedit.org) (IFDB — the Internet Fanedit Database).

## Overview

fanedit.org hosts the IFDB, a community-curated catalogue of fan-edited films and TV shows. Entries
cover cut-downs, extended editions, TV-to-movie conversions, preservations, and more. The site has no
public API, so pyfanedit scrapes HTML pages using `curl_cffi` (for TLS fingerprint bypass) and
`BeautifulSoup`, then returns structured Pydantic models.

## Quick Install

```bash
pip install pyfanedit
```

## Hello World

```python
from pyfanedit import FaneditClient

client = FaneditClient()
results, _ = client.search("star wars")
for r in results[:3]:
    print(r.title, "|", r.faneditor, "|", r.user_rating)
```

## Key Classes

| Class | Purpose | Source |
|---|---|---|
| `FaneditClient` | All user-facing methods (search, browse, detail) | `pyfanedit/client.py:27` |
| `FaneditSummary` | Lightweight record from listing/search pages | `pyfanedit/models.py:28` |
| `FaneditDetail` | Full record from a single fanedit page | `pyfanedit/models.py:51` |
| `Review` | One user or editor review | `pyfanedit/models.py:15` |
| `ReviewRatings` | Per-dimension ratings inside a review | `pyfanedit/models.py:6` |
| `Session` | HTTP layer with caching and TLS impersonation | `pyfanedit/session.py:14` |

## Contents

- [Quick Start](quickstart.md) — install, first search, pagination, common pitfalls
- [API Reference](reference.md) — every method and every model field
- [IDs, IMDB Mapping, and Metadata](ids-and-metadata.md) — identifier types and field availability matrix
- [Advanced Usage](advanced.md) — custom sessions, bulk export, extending the parser

## See also

- [fanedit.org](https://fanedit.org)
- [GitHub repository](https://github.com/OpenJarbas/pyfanedit)
