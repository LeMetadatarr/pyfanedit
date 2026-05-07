"""08 — Session injection: custom profiles, plain requests, shared cache.

Shows: FaneditClient(impersonate=...), session_factory, Session injection,
PYFANEDIT_TRANSPORT, cache inspection.
"""
import os

import requests as _requests

from pyfanedit import FaneditClient
from pyfanedit.session import Session

# --- Option A: custom curl_cffi impersonation profile ---
# Any profile supported by curl_cffi works (chrome120, chrome131, safari17_0, …)
client_a = FaneditClient(impersonate="chrome131", cache_ttl=600)
items, _ = client_a.get_latest()
print(f"Option A (chrome131): {items[0].title}")

# --- Option B: force plain requests via env var (will warn) ---
os.environ["PYFANEDIT_TRANSPORT"] = "requests"
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", RuntimeWarning)
    client_b = FaneditClient()
os.environ.pop("PYFANEDIT_TRANSPORT")
print(f"Option B (plain requests): client created")

# --- Option C: inject a requests.Session factory ---
# The factory is called with impersonate= keyword; TypeError is caught for
# factories that don't accept it.
client_c = FaneditClient(session_factory=lambda **_: _requests.Session())
print(f"Option C (factory): client created")

# --- Option D: shared pre-built Session across two clients ---
shared = Session(impersonate="safari17_0", cache_ttl=900, cache_size=1000)
client_d1 = FaneditClient(session=shared)
client_d2 = FaneditClient(session=shared)
# Both clients share the same in-process response cache.
items, _ = client_d1.get_latest()
print(f"Option D (shared session): {items[0].title}")
