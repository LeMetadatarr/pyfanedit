"""Tests for HTTP transport selection, env var override, and injection."""
from __future__ import annotations

import warnings
from unittest.mock import MagicMock

import pytest

import pyfanedit.session as session_mod
from pyfanedit.client import FaneditClient
from pyfanedit.session import Session


class _FakeResp:
    def __init__(self, text: str = "<html></html>", status: int = 200) -> None:
        self.text = text
        self.status_code = status

    def raise_for_status(self) -> None:  # noqa: D401
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _FakeUnderlying:
    """Minimal stand-in for a curl_cffi / requests Session."""

    def __init__(self) -> None:
        self.get_calls = []
        self.post_calls = []

    def get(self, url, params=None, headers=None):
        self.get_calls.append((url, params, headers))
        return _FakeResp(f"<html>GET {url}</html>")

    def post(self, url, data=None, headers=None):
        self.post_calls.append((url, data, headers))
        return _FakeResp(f"<html>POST {url}</html>")


# ---------------------------------------------------------------------------
# 1. Session injection
# ---------------------------------------------------------------------------

def test_session_factory_injection_used():
    """A custom factory is invoked instead of the auto-detected transport."""
    fake = _FakeUnderlying()
    factory = MagicMock(return_value=fake)

    sess = Session(session_factory=factory, cache_ttl=0)
    text = sess.get("/some/path", use_cache=False)

    factory.assert_called_once()
    assert "GET https://fanedit.org/some/path" in text
    assert fake.get_calls and fake.get_calls[0][0].endswith("/some/path")


def test_factory_without_impersonate_kwarg_falls_back():
    """A factory that doesn't take ``impersonate`` should still work."""
    fake = _FakeUnderlying()

    def factory():  # no kwargs
        return fake

    sess = Session(session_factory=factory)
    assert sess._session is fake


def test_client_session_injection():
    """``FaneditClient(session=...)`` reuses the provided Session."""
    fake = _FakeUnderlying()
    inner = Session(session_factory=lambda **_: fake)
    client = FaneditClient(session=inner)
    assert client._s is inner


def test_client_session_factory_passthrough():
    """``FaneditClient(session_factory=...)`` is forwarded to Session."""
    fake = _FakeUnderlying()
    client = FaneditClient(session_factory=lambda **_: fake)
    assert client._s._session is fake


# ---------------------------------------------------------------------------
# 2. PYFANEDIT_TRANSPORT=requests path emits a warning
# ---------------------------------------------------------------------------

def test_env_var_requests_warns(monkeypatch):
    """``PYFANEDIT_TRANSPORT=requests`` forces plain requests with a warning."""
    monkeypatch.setenv("PYFANEDIT_TRANSPORT", "requests")
    assert session_mod._select_transport() == "requests"

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        s = session_mod._default_session_factory()
    # Should be a plain requests.Session, not a curl_cffi one.
    import requests as _real_requests
    assert isinstance(s, _real_requests.Session)
    # And we should have warned about defended-site fallback.
    assert any(
        issubclass(w.category, RuntimeWarning) and "fanedit.org" in str(w.message)
        for w in caught
    )


# ---------------------------------------------------------------------------
# 3. PYFANEDIT_TRANSPORT=curl_cffi path (when available)
# ---------------------------------------------------------------------------

def test_env_var_curl_cffi_when_available(monkeypatch):
    """When curl_cffi is installed, the env var selects it without warnings."""
    pytest.importorskip("curl_cffi")
    monkeypatch.setenv("PYFANEDIT_TRANSPORT", "curl_cffi")
    assert session_mod._select_transport() == "curl_cffi"

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        s = session_mod._default_session_factory()
    # Should NOT have emitted the plain-requests fallback warning.
    assert not any(
        issubclass(w.category, RuntimeWarning) and "plain `requests`" in str(w.message)
        for w in caught
    )
    # Should be a curl_cffi Session.
    from curl_cffi import requests as curl_requests
    assert isinstance(s, curl_requests.Session)


def test_auto_select_prefers_curl_cffi_when_available():
    """With env var unset, auto-select picks curl_cffi if importable."""
    pytest.importorskip("curl_cffi")
    import os
    os.environ.pop("PYFANEDIT_TRANSPORT", None)
    assert session_mod._select_transport() == "curl_cffi"
