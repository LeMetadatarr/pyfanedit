# AGENTS.md — pyfanedit

Python scraping client for fanedit.org (IFDB, the Internet Fanedit Database): search, browsing, detail pages, reviewer leaderboards, news, and typed `mediavocab.Release` export.

## Setup

```bash
pip install -e .            # plain requests transport — warns, usually blocked
pip install -e .[stealth]   # adds curl_cffi for TLS fingerprint bypass (recommended for live use)
pip install -e .[test]      # pytest + curl_cffi for the test suite
```

fanedit.org uses TLS fingerprinting and Cloudflare heuristics. Without curl_cffi, the transport falls back to plain `requests` and emits a `RuntimeWarning` per request; most live requests are blocked.

## Test

```bash
pytest tests/
```

Tests are file-backed cassette-driven (curl_cffi is not vcrpy-compatible, so a home-grown cassette layer in `tests/conftest.py` stores HTML under `tests/cassettes/<module>/<key>.html`). Replay mode is default; unexpected URLs fail the test (mirrors vcrpy `record_mode="none"`). Re-record locally:

```bash
PYFANEDIT_RECORD=1 pytest tests/test_*_vcr.py
```

Test files: `test_synthetic.py` (parser unit tests), `test_client_vcr.py` (cassette-backed client), `test_converter.py` (mediavocab conversion), `test_transport.py` (transport selection/session).

## Lint/Typecheck

Ruff via the gh-automations lint workflow (no local ruff/mypy config in `pyproject.toml`; no pre-commit). No type checker configured.

## Layout

- `pyfanedit/client.py` — `FaneditClient`, the public API (curated lists, search, tag browsing, categories, detail, reviews, reviewer leaderboard, news). All listing methods return `(list[FaneditSummary], next_url | None)`.
- `pyfanedit/parsers.py` — BeautifulSoup HTML parsers (largest module); turns IFDB pages into models. This is where upstream HTML drift hits.
- `pyfanedit/models.py` — Pydantic v2 models: `FaneditSummary`, `FaneditDetail`, `Review`, `ReviewRatings`, `ReviewerEntry`, `UserReviewEntry`, `NewsArticle`.
- `pyfanedit/converters.py` — `fanedit_to_release` maps IFDB models to typed `mediavocab` objects (`Work`, `Release`, `WorkRelation`, credits).
- `pyfanedit/session.py` — HTTP layer: transport auto-detection (`curl_cffi` vs `requests`), `PYFANEDIT_TRANSPORT` override, TTL+LRU response cache, injectable `session_factory`.
- `pyfanedit/version.py` — version string (do not edit; see Conventions).
- `docs/` — getting-started, reference, models, transport, converter, ids-and-metadata.
- `examples/` — 10 runnable scripts (quickstart, search, detail, curated lists, reviews, news, mediavocab export, custom session, watchlist, advanced pipeline).

## Conventions (Org hard rules)

- Branches: `dev` (work) and `master` (stable). NEVER `main`.
- Never edit `pyfanedit/version.py`; gh-automations bumps semver from conventional-commit prefixes (`feat:` / `fix:` / `feat!:`).
- New repos private by default; do not make public without asking.
- Commit identity: JarbasAi <jarbasai@mailfence.com>.
- Reference `OpenVoiceOS/gh-automations` reusable workflows at `@dev`.
- No Neon / `neon-*` references.
- No meta-commentary in docs/commits/PRs/code: describe current state only, no history, dates, or "before times".
- CI is provided by OpenVoiceOS/gh-automations.

## Gotchas

- The `pyproject.toml` `[project.urls] Homepage` points at `OpenJarbas/pyfanedit` while the GitHub remote is `JarbasAl/pyfanedit` — the URL is stale relative to the actual repo.
- mediavocab is a hard dependency (`mediavocab>=1.0.0`), not optional — importing `pyfanedit` always pulls it in.
- `session.py` builds a module-level `default_session` at import time with warnings suppressed; it can be `None` if construction fails.
- `MOVIE_TO_TV` recuts convert to `MediaType.EPISODIC_SERIES` per the mediavocab "one Work, one MediaType" axiom — not a movie.
- fanedit subtypes absent from the mediavocab foundation (`fanfix`, `fanmix`, `fanedit_short`) are stored in the free-text subtype slot in `Work.extra`, not as first-class `VariantKind` values.
- Repo root contains tracked data artefacts (`fanfix_edits.jsonl`, `watchlist_state.json`, `.coverage`) — example/scratch output, not package data.
