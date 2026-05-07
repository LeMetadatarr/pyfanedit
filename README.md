# pyfanedit

Python scraping client for [fanedit.org](https://fanedit.org) (IFDB — the Internet Fanedit Database).

## Install

```bash
pip install pyfanedit            # plain `requests` transport (likely blocked)
pip install pyfanedit[stealth]   # recommended — adds curl_cffi
```

### HTTP transport

fanedit.org is heavily defended against scraping (TLS fingerprint and UA
heuristics), so `pyfanedit` prefers [`curl_cffi`](https://pypi.org/project/curl-cffi/)
to impersonate a real browser. It is now an **optional** dependency,
installed via the `[stealth]` extra. Without it `pyfanedit` falls back to
plain `requests` and emits a `RuntimeWarning` — most requests will be
blocked by Cloudflare in that mode.

You can pin the transport with the `PYFANEDIT_TRANSPORT` env var:

```bash
PYFANEDIT_TRANSPORT=curl_cffi   # explicit (default if available)
PYFANEDIT_TRANSPORT=requests    # force plain requests (warns)
```

You can also inject your own session — useful for tests, alt
impersonation profiles, or sharing a session across clients:

```python
from pyfanedit import FaneditClient
from pyfanedit.session import Session

# Custom impersonation profile (curl_cffi only)
client = FaneditClient(impersonate="chrome131")

# Custom factory
import requests
client = FaneditClient(session_factory=lambda **_: requests.Session())

# Pre-built Session (e.g. shared cache)
shared = Session(cache_ttl=900)
client = FaneditClient(session=shared)
```


## Quick Start

```python
from pyfanedit import FaneditClient

client = FaneditClient()
results, _ = client.search("star wars")
detail = client.get_detail(results[0].url)
print(detail.title, detail.imdb_id, detail.time_cut)
```

## Typed `mediavocab.Release` output

`pyfanedit` ships a converter that turns scraped fanedits into typed
[`mediavocab.Release`](https://github.com/JarbasAl/mediavocab) objects so
they slot into the same vocabulary as every other media provider:

```python
from pyfanedit import FaneditClient, fanedit_to_release
from mediavocab import VariantKind, MediaType, RelationRole, WorkRelationKind

client = FaneditClient()

# Look up every fanedit of a specific film by exact original-title match.
summaries = client.search_by_original_title("Star Wars")

for summary in summaries[:3]:
    detail = client.get_detail(summary.url)
    release = fanedit_to_release(detail)
    work = release.work

    # Typed mediavocab fields populated from IFDB free-text:
    #   work.runtime         — seconds, parsed from "Fanedit Running Time"
    #   work.edition         — lifted from titles like "...: Director's Cut"
    #   work.source_format   — normalised from "Release Information"
    #                          (BD-25, WEB-DL, DVD, …)
    #   work.content_genres  — inherited from the source movie's tags
    #   work.variant_kind    — FANEDIT / EXTENDED / TV_TO_MOVIE / …
    #   release.resolution / release.hdr / release.audio_channels
    #                        — lifted from "Available In" when present
    #   release.release_date — parsed by mediavocab's IsoDate validator

    # The faneditor is the recut's EDITOR (not the source film's CREATOR).
    for credit in work.credits:
        if credit.relation_role is RelationRole.EDITOR:
            print("editor:", credit.entity.name)

    # Source IMDb id stored as `derived_from_imdb` (the fanedit itself has
    # no IMDb listing — its source movie does).
    print(work.external_ids.get("derived_from_imdb"))

    # mediavocab's `Work` has no first-class `relations` field, so the
    # FANEDIT_OF backlink to the source Work is serialised into
    # `work.extra["work_relations"]`. Round-trip with `WorkRelation(**rel)`.
    for rel in work.extra.get("work_relations", []):
        if rel.get("kind") == WorkRelationKind.FANEDIT_OF.value:
            print("source:", rel["target"]["title"])
```

`MOVIE_TO_TV` re-cuts produce a Work with `media_type=EPISODIC_SERIES`
per the mediavocab "one Work, one MediaType" axiom.

## Features

- Search the IFDB by keyword, scope, and sort order
- Browse named categories (`fanfix`, `fanmix`, `extended`, `tv_to_movie`, and more)
- Browse by franchise, editor name, release year, or any other tag
- Curated lists: latest, top trusted-reviewer rated, top user rated, most popular, award winners
- Full detail pages: genre, cuts, intention, IMDB ID, editor and user reviews
- **Reviewer leaderboard** — paginated list of top reviewers with helpful-vote stats
- **Reviews by user** — all reviews written by a specific user, with eight sort orders
- **News** — front-page article cards and full article bodies with linked IFDB URLs
- In-process LRU cache with configurable TTL; thread-safe

## Documentation

- [Quick Start](docs/quickstart.md)
- [API Reference](docs/reference.md)
- [IDs, IMDB Mapping, and Metadata](docs/ids-and-metadata.md)
- [Advanced Usage](docs/advanced.md)

## License

Apache 2.0
