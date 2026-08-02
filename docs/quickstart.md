# Quick Start

## Install

```bash
pip install pyfanedit
```

For a development (editable) install from a local clone:

```bash
git clone https://github.com/LeMetadatarr/pyfanedit
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

`search` returns a tuple: a list of `FaneditSummary` objects and a URL for the next page (or `None` if there is no next page).

## Browse a Category

fanedit.org organizes edits into named categories. Use `get_category` with one of the built-in keys:

```python
items, next_page = client.get_category("fanfix")
for item in items:
    print(item.title, "| editor:", item.editor_rating, "| user:", item.user_rating)
```

Available category keys: `fanfix`, `fanmix`, `extended`, `tv_to_movie`, `movie_to_tv`, `shorts`, `special`, `documentary`, `preservation`, `unapproved`.

## Get Full Details for One Edit

Listing pages return lightweight summaries. To get the full record (genre, cuts list, intention, reviews), fetch the detail page:

```python
results, _ = client.search("blade runner")
detail = client.get_detail(results[0].url)

print(detail.title)
print("Genre:", detail.genre)
print("IMDB ID:", detail.imdb_id)
print("Cut time:", detail.time_cut)
print("Reviews:", len(detail.user_reviews))
```

`get_detail` (`pyfanedit/client.py:232`) accepts either the full URL from a `FaneditSummary.url` or a bare slug such as `"blade-runner-final-cut-redux"`.

## Follow Pagination with `iter_search`

`iter_search` is a generator. It fetches subsequent pages automatically until results run out or an optional `max_pages` limit is reached:

```python
for edit in client.iter_search("marvel", max_pages=3):
    print(edit.title)
```

`iter_category` and `iter_by_tag` work the same way for categories and tag browsing.

## Common Pitfalls

**Rate limiting.** fanedit.org does not publish rate limits, but sending back-to-back requests risks a temporary block. Add a small sleep when iterating many pages:

```python
import time
from pyfanedit import FaneditClient

client = FaneditClient()
for edit in client.iter_category("fanfix"):
    print(edit.title)
    time.sleep(0.5)
```

**Lazy-loaded cover images.** On listing pages, cover images can sit in the `data-jr-src` attribute instead of `src`. The parser checks both, but an image whose `src` is a `data:` URI (placeholder) is set to `None` in `cover_url`. Do not assume `cover_url` is always set.

**IMDB ID not always present.** `FaneditDetail.imdb_id` comes from the first IMDB link found on the detail page. If the editor did not link to IMDB, or the URL is malformed (a nested `https://fanedit.org/...https://imdb.com/...` pattern), the value can be `None` or incorrect. Check for `None` before you use it.

**`fanedit_id` is detail-only.** The WordPress post ID (`fanedit_id`) comes from a CSS class on the `<body>` element. This class only appears on individual detail pages, not listing pages. `fanedit_id` is always `None` on `FaneditSummary`.

**curl_cffi.** The HTTP layer uses `curl_cffi` instead of `requests`, so outgoing TLS handshakes match a real browser fingerprint. This reduces the chance of bot-detection blocks. No configuration is needed.

---
[Home](index.md) · [API Reference →](reference.md)
