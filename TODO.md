# TODO — pyfanedit

## Open issues

- [ ] #2 Dependency Dashboard (Renovate bot meta-issue)

## Gaps

- [ ] `pyproject.toml` `Homepage` URL points to `OpenJarbas/pyfanedit`; remote is `JarbasAl/pyfanedit` — fix the stale URL.
- [ ] No type checker (mypy) configured; lint is ruff-only via gh-automations.
- [ ] Tracked scratch/data artefacts in repo root (`fanfix_edits.jsonl`, `watchlist_state.json`, `.coverage`) — confirm whether these belong in the repo or should be gitignored.
- [ ] No `repo-health`/`pip_audit` gaps detected — standard gh-automations workflows present (build-tests, coverage, lint, license_check, release_workflow, publish_stable, release-preview, plus nightly-live drift check).

## Code TODOs

None found. (No TODO/FIXME/XXX/HACK markers in `pyfanedit/` or `tests/`.)
