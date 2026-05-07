# Transport and Session Injection

## Why curl_cffi

fanedit.org blocks plain `requests` via TLS fingerprinting and Cloudflare heuristics. `pyfanedit[stealth]` bundles `curl_cffi`, which impersonates a real browser at the TLS handshake level. Without it, a `RuntimeWarning` is emitted on every `Session` construction and most requests will be blocked.

## Auto-detection

`Session` resolves the transport at construction time: — `pyfanedit/session.py:31`

1. Check `PYFANEDIT_TRANSPORT` env var.
2. If not set, try to `import curl_cffi`. Use it if importable.
3. Fall back to plain `requests` with a `RuntimeWarning`.

```bash
PYFANEDIT_TRANSPORT=curl_cffi   # explicit (default when installed)
PYFANEDIT_TRANSPORT=requests    # force plain requests (warns)
```

## Session Parameters

`Session.__init__` — `pyfanedit/session.py:74`

| Parameter | Default | Description |
|---|---|---|
| `impersonate` | `"chrome120"` | curl_cffi browser profile (ignored for plain requests) |
| `cache_ttl` | `300.0` | Seconds before a cached URL expires; `0` disables caching |
| `cache_size` | `512` | Maximum number of cached responses; oldest evicted when full |
| `session_factory` | `None` | Callable returning the raw HTTP session (bypasses auto-detection) |

Cache key is `(method, url, sorted_params)`. The cache dict is guarded by a `threading.Lock` — a single `Session` / `FaneditClient` is safe to use from multiple threads simultaneously. — `pyfanedit/session.py:92`

## Injection Patterns

### Custom impersonation profile

```python
from pyfanedit import FaneditClient

client = FaneditClient(impersonate="chrome131")
```

Any profile name supported by `curl_cffi` works. Consult the curl_cffi docs for the full list.

### Disable cache

```python
client = FaneditClient(cache_ttl=0)
```

### Inject a pre-built Session

```python
from pyfanedit import FaneditClient
from pyfanedit.session import Session

shared = Session(impersonate="safari17_0", cache_ttl=900, cache_size=1000)
client = FaneditClient(session=shared)
```

When `session` is passed, `impersonate` and `cache_ttl` on the `FaneditClient` constructor are ignored.

### Inject a factory (e.g. for tests)

```python
import requests
from pyfanedit import FaneditClient

client = FaneditClient(session_factory=lambda **_: requests.Session())
```

The factory is called with `impersonate=...` as a keyword argument. If the factory does not accept that kwarg (as with `requests.Session`), the `TypeError` is caught and it is called with no arguments. — `pyfanedit/session.py:83`

### Share a session across clients

```python
from pyfanedit import FaneditClient
from pyfanedit.session import Session

session = Session(cache_ttl=600)
client_a = FaneditClient(session=session)
client_b = FaneditClient(session=session)
```

The response cache is shared; a hit from either client benefits both.

## Thread Safety

The cache lock is per-`Session`. Sharing a `Session` across threads is safe. Sharing across processes is not — the cache is in-process only.

## See also

- [FaneditClient Reference](reference.md)
- [Getting Started](getting-started.md)
