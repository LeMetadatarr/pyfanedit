"""HTTP layer using curl_cffi to bypass TLS fingerprinting."""
from __future__ import annotations

import time
from threading import Lock
from typing import Any, Dict, Mapping, Optional, Tuple

from curl_cffi import requests

SITE_URL = "https://fanedit.org"
_CacheKey = Tuple[str, str, Tuple[Tuple[str, str], ...]]


class Session:
    def __init__(
        self,
        impersonate: str = "chrome120",
        cache_ttl: float = 300.0,
        cache_size: int = 512,
    ) -> None:
        self._session = requests.Session(impersonate=impersonate)
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


default_session = Session()
