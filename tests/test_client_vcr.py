"""Cassette-backed parser tests for the fanedit.org scraper.

These tests replay real captured HTML responses against the parser so
upstream HTML changes surface as test failures rather than silent empty
results.

Re-record cassettes (hits fanedit.org live)::

    PYFANEDIT_RECORD=1 pytest tests/test_client_vcr.py

The nightly CI workflow runs in record mode against the live site so
cassette drift surfaces within 24h.
"""
from __future__ import annotations

from pyfanedit.client import FaneditClient
from pyfanedit.models import (
    FaneditDetail, FaneditSummary, NewsArticle, ReviewerEntry,
)


def test_get_latest_returns_summaries(cassette_session):
    items, _next = FaneditClient().get_latest(page=1)
    assert items, "expected at least one fanedit"
    first = items[0]
    assert isinstance(first, FaneditSummary)
    assert first.title
    assert first.url


def test_get_category_fanfix(cassette_session):
    items, _next = FaneditClient().get_category("fanfix", page=1)
    assert items
    assert all(isinstance(i, FaneditSummary) for i in items)


def test_get_top_user_rated(cassette_session):
    items, _next = FaneditClient().get_top_user_rated(page=1)
    assert items
    assert all(isinstance(i, FaneditSummary) for i in items)


def test_get_most_popular(cassette_session):
    items, _next = FaneditClient().get_most_popular(page=1)
    assert items


def test_get_reviewer_rank(cassette_session):
    items, _next = FaneditClient().get_reviewer_rank(page=1)
    assert items
    assert all(isinstance(i, ReviewerEntry) for i in items)


def test_get_latest_user_reviews(cassette_session):
    items, _next = FaneditClient().get_latest_user_reviews(page=1)
    assert items
    assert all(isinstance(i, FaneditSummary) for i in items)


def test_get_news_listing(cassette_session):
    items = FaneditClient().get_news()
    assert items
    assert all(isinstance(i, NewsArticle) for i in items)


def test_get_detail_round_trip(cassette_session):
    """Pick a fanedit from the latest listing, then fetch its detail page."""
    items, _next = FaneditClient().get_latest(page=1)
    target = items[0]
    detail = FaneditClient().get_detail(target.url)
    assert isinstance(detail, FaneditDetail)
    assert detail.title
