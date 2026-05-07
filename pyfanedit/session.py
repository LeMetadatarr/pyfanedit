"""HTTP layer with optional curl_cffi for TLS fingerprint bypass.

By default this module attempts to use ``curl_cffi`` so that requests to
fanedit.org bypass TLS fingerprinting and Cloudflare-style heuristics. If
``curl_cffi`` is not installed (or the user explicitly opts out via
``PYFANEDIT_TRANSPORT=requests``), it falls back to plain ``requests`` and
emits a warning — fanedit.org is heavily defended and will likely block
plain requests. Install with the ``[stealth]`` extra to enable curl_cffi:

    pip install pyfanedit[stealth]

The transport can also be controlled via the ``PYFANEDIT_TRANSPORT`` env
var (``curl_cffi`` or ``requests``).

Callers may inject their own ``session_factory`` callable into ``Session``
to bypass auto-detection entirely (useful for tests or custom clients).
"""
from __future__ import annotations

import os
import time
import warnings
from threading import Lock
from typing import Any, Callable, Dict, Mapping, Optional, Tuple

SITE_URL = "https://fanedit.org"
_CacheKey = Tuple[str, str, Tuple[Tuple[str, str], ...]]


def _select_transport() -> str:
    """Resolve the configured transport name (``curl_cffi`` or ``requests``)."""
    requested = (os.environ.get("PYFANEDIT_TRANSPORT") or "").strip().lower()
    if requested in ("curl_cffi", "curl-cffi", "curlcffi"):
        return "curl_cffi"
    if requested in ("requests", "plain"):
        return "requests"
    # Auto: prefer curl_cffi if importable.
    try:
        import curl_cffi  # noqa: F401
        return "curl_cffi"
    except Exception:
        return "requests"


def _default_session_factory(impersonate: str = "chrome120"):
    """Build a transport session per ``PYFANEDIT_TRANSPORT`` / availability."""
    transport = _select_transport()
    if transport == "curl_cffi":
        try:
            from curl_cffi import requests as curl_requests
            return curl_requests.Session(impersonate=impersonate)
        except ImportError:
            warnings.warn(
                "PYFANEDIT_TRANSPORT=curl_cffi requested but curl_cffi is not "
                "installed; falling back to plain `requests`. fanedit.org is "
                "heavily defended and will likely block plain requests. "
                "Install with `pip install pyfanedit[stealth]`.",
                RuntimeWarning,
                stacklevel=2,
            )
    # Plain requests fallback.
    import requests as _requests
    warnings.warn(
        "pyfanedit is using plain `requests` as its HTTP transport. "
        "fanedit.org is heavily defended and will likely block these "
        "requests. Install `pip install pyfanedit[stealth]` (or unset "
        "PYFANEDIT_TRANSPORT=requests) to enable curl_cffi.",
        RuntimeWarning,
        stacklevel=2,
    )
    return _requests.Session()


class Session:
    def __init__(
        self,
        impersonate: str = "chrome120",
        cache_ttl: float = 300.0,
        cache_size: int = 512,
        session_factory: Optional[Callable[..., Any]] = None,
    ) -> None:
        if session_factory is not None:
            try:
                self._session = session_factory(impersonate=impersonate)
            except TypeError:
                # Factory may not accept impersonate kwarg (e.g. plain requests).
                self._session = session_factory()
        else:
            self._session = _default_session_factory(impersonate=impersonate)
        self.cache_ttl = cache_ttl
        self.cache_size = cache_size
        self._cache: Dict[_CacheKey, Tuple[float, str]] = {}
        self._lock = Lock()

    def _key(self, url: str, params: Optional[Mapping[str, Any]]) -> _CacheKey:
        items = tuple(sorted((k, str(v)) for k, v in (params or {}).items()))
        return ("GET", url, items)

    def _cache_get(self, key: _CacheKey) -> Optional[str]:
        with self._lock:
            hit = self._cache.get(key)
        if hit is None:
            return None
        ts, text = hit
        if self.cache_ttl and (time.time() - ts) > self.cache_ttl:
            with self._lock:
                self._cache.pop(key, None)
            return None
        return text

    def _cache_put(self, key: _CacheKey, text: str) -> None:
        if not self.cache_size:
            return
        with self._lock:
            if len(self._cache) >= self.cache_size and self._cache:
                oldest = min(self._cache.items(), key=lambda kv: kv[1][0])[0]
                self._cache.pop(oldest, None)
            self._cache[key] = (time.time(), text)

    def get(
        self,
        path: str,
        params: Optional[Mapping[str, Any]] = None,
        use_cache: bool = True,
    ) -> str:
        url = path if path.startswith("http") else SITE_URL + "/" + path.lstrip("/")
        key = self._key(url, params)
        if use_cache:
            cached = self._cache_get(key)
            if cached is not None:
                return cached
        r = self._session.get(url, params=params, headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
        r.raise_for_status()
        if use_cache:
            self._cache_put(key, r.text)
        return r.text

    def post(self, path: str, data: Optional[Mapping[str, Any]] = None) -> str:
        url = path if path.startswith("http") else SITE_URL + "/" + path.lstrip("/")
        r = self._session.post(url, data=data, headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": SITE_URL + "/fanedit-search/",
        })
        r.raise_for_status()
        return r.text


def _make_default_session() -> Optional[Session]:
    """Best-effort module-level default; suppress warnings on import."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return Session()
    except Exception:
        return None


default_session = _make_default_session()
