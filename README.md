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
