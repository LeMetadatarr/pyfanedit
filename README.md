# pyfanedit

Python scraping client for [fanedit.org](https://fanedit.org) (IFDB — the Internet Fanedit Database).

## Install

```bash
pip install pyfanedit
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
from mediavocab import VariantKind, MediaType, WorkRelationKind

client = FaneditClient()

# Look up every fanedit of a specific film by exact original-title match.
summaries = client.search_by_original_title("Star Wars")

for summary in summaries[:3]:
    detail = client.get_detail(summary.url)
    release = fanedit_to_release(detail)

    assert release.work.media_type == MediaType.MOVIE
    assert release.variant_kind in {
        VariantKind.FANEDIT, VariantKind.EXTENDED,
        VariantKind.TV_TO_MOVIE, VariantKind.MOVIE_TO_TV,
        VariantKind.PRESERVATION, VariantKind.OTHER,
    }
    # Source IMDb id stored as `derived_from_imdb` (the fanedit itself has
    # no IMDb listing — its source movie does).
    print(release.work.external_ids.get("derived_from_imdb"))
    # FANEDIT_OF link back to the source Work travels in `work.extra`.
    print(release.work.extra.get("work_relations"))
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
