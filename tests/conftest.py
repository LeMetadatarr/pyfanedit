"""Shared pytest config — file-backed cassettes for HTTP scraper tests.

pyfanedit talks to fanedit.org through curl_cffi (TLS fingerprint bypass),
which vcrpy cannot intercept (it hooks urllib3/http.client, not curl). So
we use an equivalent home-grown cassette layer: HTML responses are stored
under ``tests/cassettes/<module>/<key>.html`` keyed by ``GET <path>?<params>``.

Re-record cassettes by setting the env var::

    PYFANEDIT_RECORD=1 pytest tests/test_*_vcr.py

In normal (replay) mode any unexpected URL fails the test, mirroring
vcrpy's ``record_mode="none"``. The nightly CI workflow runs in record
mode against the live site so upstream drift surfaces within 24h.
"""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any, Mapping, Optional

import pytest

from pyfanedit import session as _session_mod


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9._-]+", "_", text).strip("_")
    return s[:120] or "root"


def _cassette_key(method: str, url: str, params: Optional[Mapping[str, Any]]) -> str:
    items = sorted((k, str(v)) for k, v in (params or {}).items())
    qs = "&".join(f"{k}={v}" for k, v in items)
    raw = f"{method} {url}?{qs}"
    digest = hashlib.sha1(raw.encode()).hexdigest()[:8]
    # Strip the SITE_URL prefix for readable filenames.
    short = url.replace(_session_mod.SITE_URL, "").lstrip("/") or "root"
    return f"{_slugify(short)}__{_slugify(qs) if qs else 'noparams'}__{digest}"


class _CassetteSession:
    """Drop-in replacement for ``pyfanedit.session.Session`` for tests."""

    def __init__(self, cassette_dir: Path, record: bool) -> None:
        self.cassette_dir = cassette_dir
        self.record = record
        self.cassette_dir.mkdir(parents=True, exist_ok=True)
        self._real: Optional[_session_mod.Session] = None

    def _resolve_url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return _session_mod.SITE_URL + "/" + path.lstrip("/")

    def _read_or_record(
        self, method: str, path: str, params: Optional[Mapping[str, Any]] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> str:
        url = self._resolve_url(path)
        key = _cassette_key(method, url, params or data)
        cassette = self.cassette_dir / f"{key}.html"
        if cassette.exists() and not self.record:
            return cassette.read_text(encoding="utf-8")
        if not self.record:
            raise AssertionError(
                f"Missing cassette {cassette} for {method} {url} params={params} "
                f"data={data}. Re-record with PYFANEDIT_RECORD=1."
            )
        # Record mode: hit the live site.
        if self._real is None:
            self._real = _session_mod.Session()
        if method == "GET":
            text = self._real.get(path, params=params, use_cache=False)
        else:
            text = self._real.post(path, data=data)
        cassette.write_text(text, encoding="utf-8")
        return text

    # Mirror Session API used by FaneditClient.
    def get(self, path: str, params: Optional[Mapping[str, Any]] = None,
            use_cache: bool = True) -> str:
        return self._read_or_record("GET", path, params=params)

    def post(self, path: str, data: Optional[Mapping[str, Any]] = None) -> str:
        return self._read_or_record("POST", path, data=data)


@pytest.fixture
def cassette_session(request, monkeypatch) -> _CassetteSession:
    """Provides a cassette-backed Session and patches it into FaneditClient."""
    record = bool(int(os.environ.get("PYFANEDIT_RECORD", "0") or "0"))
    module_file = Path(request.module.__file__)
    cassette_dir = module_file.parent / "cassettes" / module_file.stem
    sess = _CassetteSession(cassette_dir, record=record)

    # Replace Session class so FaneditClient() picks up the cassette session.
    import pyfanedit.client as _client
    monkeypatch.setattr(_client, "Session", lambda *a, **kw: sess)
    return sess
