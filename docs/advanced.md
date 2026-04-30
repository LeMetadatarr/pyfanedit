# Advanced Usage

## Custom Session Configuration

`FaneditClient` creates a `Session` internally. If you need different TLS impersonation
or cache behaviour, construct the client with custom parameters:

```python
from pyfanedit import FaneditClient

# Impersonate Firefox 117 instead of Chrome 120
client = FaneditClient(impersonate="firefox117")

# Disable caching entirely
client = FaneditClient(cache_ttl=0)

# Keep cache for 10 minutes, hold up to 1 000 entries
# (cache_size is a Session parameter — not exposed on FaneditClient directly)
from pyfanedit.session import Session
from pyfanedit.parsers import parse_listing_page, parse_detail_page

session = Session(impersonate="chrome120", cache_ttl=600.0, cache_size=1000)
```

The `impersonate` string is forwarded directly to `curl_cffi.requests.Session` —
`pyfanedit/session.py:21`. Consult the curl_cffi documentation for the full list of
supported browser profile names.

### Cache Behaviour

`Session` stores responses in an in-process LRU-style dict. — `pyfanedit/session.py:14`

- Cache key is `(method, url, sorted_params)`.
- When the cache reaches `cache_size` entries, the oldest entry (by insertion timestamp)
  is evicted.
- Entries older than `cache_ttl` seconds are considered stale and re-fetched.
- The cache dict is protected by a `threading.Lock`, making the session safe to use from
  multiple threads simultaneously — `pyfanedit/session.py:6`.

---

## Thread Safety

The `Lock` in `Session._lock` guards all reads and writes to `_cache`. It is safe to
share a single `FaneditClient` (and therefore a single `Session`) across threads:

```python
import threading
from pyfanedit import FaneditClient

client = FaneditClient()

def fetch(slug):
    detail = client.get_detail(slug)
    print(detail.title)

threads = [threading.Thread(target=fetch, args=(s,)) for s in ["my-edit", "other-edit"]]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

The underlying `curl_cffi` session object is not covered by the lock — only the response
cache is. Do not share a single `Session` instance across processes.

---

## Iterating All Fanedits in a Category

```python
import time
from pyfanedit import FaneditClient

client = FaneditClient()

for edit in client.iter_category("fanfix"):
    print(edit.title, edit.user_rating)
    time.sleep(0.3)   # be polite
```

`iter_category` — `pyfanedit/client.py:52` — stops automatically when the listing page
returns no next-page URL. Set `max_pages` if you only want the first N pages.

---

## Building a Local Dataset

The following example streams every FanFix edit to a JSONL file, fetching the detail page
for each one to capture the full metadata:

```python
import json
import time
from pyfanedit import FaneditClient

client = FaneditClient(cache_ttl=3600)  # long TTL for batch work

with open("fanfix.jsonl", "w") as fh:
    for summary in client.iter_category("fanfix"):
        try:
            detail = client.get_detail(summary.url)
            fh.write(detail.model_dump_json() + "\n")
        except Exception as exc:
            print(f"Skipping {summary.url}: {exc}")
        time.sleep(0.5)
```

`model_dump_json()` is a Pydantic v2 method available on all models. To export as a plain
dict instead, use `detail.model_dump()`.

---

## Franchise and Tag Browsing

### Known `tag_type` Values

`get_by_tag(tag_type, tag_value)` — `pyfanedit/client.py:120` — constructs the path
`fanedit-search/tag/<tag_type>/<tag_value>/`. The following `tag_type` values are
documented in the client:

| `tag_type` | Example `tag_value` | Description |
|---|---|---|
| `franchise` | `"star-wars"` | Film/show franchise |
| `faneditorname` | `"john-doe"` | Editor's username slug |
| `originalmovietitle` | `"the-matrix"` | Slugified source title |
| `fanedittype` | `"fanfix"` | Edit category |
| `faneditreleasedate` | `"2023"` | Release year |
| `award` | `"fanedit-of-the-month"` | Award winner tag |

Any tag slug visible in a fanedit.org tag URL will work, not just those listed above.

```python
# All edits by a specific editor
for edit in client.iter_by_tag("faneditorname", "editor-slug"):
    print(edit.title)

# All Fanedit of the Month winners (convenience wrapper)
items, _ = client.get_award_winners()
```

---

## `ORDER_CHOICES` Explained

Pass any value from `ORDER_CHOICES` as the `order` parameter to `search` or `iter_search`.

| Value | Sort order |
|---|---|
| `"rdate"` | Fanedit release date, newest first (default) |
| `"date"` | Date added to IFDB, newest first |
| `"modified"` | Last modified in IFDB, newest first |
| `"alpha"` | A–Z by title |
| `"rratio"` | Highest trusted-reviewer rating first |
| `"rvote"` | Most votes first |

```python
# Find the most-voted Star Wars fanedits
for edit in client.iter_search("star wars", order="rvote", max_pages=2):
    print(edit.title, edit.user_rating_count)
```

---

## Extending the Parser: `extra_fields` and Adding New Field Mappings

### Reading `extra_fields`

Any `jrFieldRow` on a detail page whose label is not in `_DETAIL_FIELD_MAP` ends up in
`FaneditDetail.extra_fields` as `{raw_label: text_value}`.

```python
detail = client.get_detail("some-fanedit")
if detail.extra_fields:
    print("Unmapped fields:", detail.extra_fields)
```

This is useful for debugging when a field appears on the page but is `None` on the model.

### Adding a New Mapped Field

To permanently map a new label to a model field:

1. Add the label (lowercase, with trailing colon) and the desired field name to
   `_DETAIL_FIELD_MAP` in `pyfanedit/parsers.py:12`.
2. Add the corresponding field to `FaneditDetail` in `pyfanedit/models.py:51`.

Example — suppose IFDB adds a `"language:"` field:

```python
# pyfanedit/parsers.py
_DETAIL_FIELD_MAP = {
    ...
    "language:": "language",
}

# pyfanedit/models.py
class FaneditDetail(BaseModel):
    ...
    language: Optional[str] = None
```

No other changes are needed. The field will be populated automatically on the next parse.

### Adding a Field to Summaries

Listing pages expose fewer fields. To add a new summary field, update `_SUMMARY_FIELD_MAP`
in `pyfanedit/parsers.py:33` and add the field to `FaneditSummary` in
`pyfanedit/models.py:28`.

---

## See also

- [API Reference](reference.md)
- [IDs, IMDB Mapping, and Metadata](ids-and-metadata.md)
- [Quick Start](quickstart.md)
