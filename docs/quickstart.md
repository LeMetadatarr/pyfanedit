# Quick Start

## Install

```bash
pip install pyfanedit
```

For a development (editable) install from a local clone:

```bash
git clone https://github.com/OpenJarbas/pyfanedit
cd pyfanedit
pip install -e ".[test]"
```

## First Search

```python
from pyfanedit import FaneditClient

client = FaneditClient()
results, next_page = client.search("batman")
for r in results:
    print(r.title, "|", r.faneditor, "|", r.release_date)
```

`search` returns a tuple: a list of `FaneditSummary` objects and a URL for the next page
(or `None` if there is no next page).

## Browse a Category

fanedit.org organises edits into named categories. Use `get_category` with one of the built-in keys:

```python
items, next_page = client.get_category("fanfix")
for item in items:
    print(item.title, "| editor:", item.editor_rating, "| user:", item.user_rating)
```

Available category keys: `fanfix`, `fanmix`, `extended`, `tv_to_movie`, `movie_to_tv`,
`shorts`, `special`, `documentary`, `preservation`, `unapproved`.

## Get Full Details for One Edit

Listing pages return lightweight summaries. To get the full record — genre, cuts list,
intention, reviews — fetch the detail page:

```python
results, _ = client.search("blade runner")
detail = client.get_detail(results[0].url)

print(detail.title)
print("Genre:", detail.genre)
print("IMDB ID:", detail.imdb_id)
print("Cut time:", detail.time_cut)
print("Reviews:", len(detail.user_reviews))
```

`get_detail` accepts either the full URL from a `FaneditSummary.url` or a bare slug such as
`"blade-runner-final-cut-redux"`. — `pyfanedit/client.py:176`

## Follow Pagination with `iter_search`

`iter_search` is a generator that automatically fetches subsequent pages until results are
exhausted or an optional `max_pages` limit is reached:

```python
for edit in client.iter_search("marvel", max_pages=3):
    print(edit.title)
```

The equivalent exists for categories (`iter_category`) and tag browsing (`iter_by_tag`).

## Common Pitfalls

**Rate limiting.** fanedit.org does not publish rate limits, but hammering the site with
back-to-back requests risks a temporary block. Add a small sleep when iterating many pages:

```python
import time
from pyfanedit import FaneditClient

client = FaneditClient()
for edit in client.iter_category("fanfix"):
    print(edit.title)
    time.sleep(0.5)
```

**Lazy-loaded cover images.** On listing pages, cover images may be stored in the
`data-jr-src` attribute rather than `src`. The parser checks both, but images whose
`src` is a `data:` URI (placeholder) are silently set to `None` in `cover_url`.
Do not assume `cover_url` is always populated.

**IMDB ID not always present.** `FaneditDetail.imdb_id` is extracted from the first IMDB
link found on the detail page. If the editor did not link to IMDB, or the URL is malformed
(a nested `https://fanedit.org/...https://imdb.com/...` pattern), the value may be `None`
or incorrect. Always guard against `None` before using it.

**`fanedit_id` is detail-only.** The WordPress post ID (`fanedit_id`) is read from a CSS
class on the `<body>` element, which only appears on individual detail pages, not listing
pages. It is always `None` on `FaneditSummary`.

**curl_cffi.** The HTTP layer uses `curl_cffi` instead of `requests` so that outgoing TLS
handshakes match a real browser fingerprint, reducing the chance of bot-detection blocks.
No configuration is needed — it works out of the box.

## See also

- [API Reference](reference.md)
- [IDs, IMDB Mapping, and Metadata](ids-and-metadata.md)
- [Advanced Usage](advanced.md)
