"""Synthetic-HTML coverage tests for pyfanedit.

These tests fabricate small, deterministic HTML snippets that exercise
the parser branches (and the FaneditClient methods that wrap them) which
are not covered by the live cassettes. They also mock the curl_cffi
session at the response level to cover ``pyfanedit.session.Session``.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import pyfanedit
from pyfanedit import (
    FaneditClient,
    FaneditDetail,
    FaneditSummary,
    NewsArticle,
    Review,
    ReviewerEntry,
    ReviewRatings,
    UserReviewEntry,
    fanedit_to_release,
)
from pyfanedit.client import CATEGORIES
from pyfanedit.converters import (
    _extract_edition,
    _parse_available_in,
    _parse_runtime_seconds,
    _parse_source_format,
)
from pyfanedit.parsers import (
    parse_detail_page,
    parse_listing_page,
    parse_news_article,
    parse_news_listing,
    parse_reviewer_rank_page,
    parse_user_reviews_page,
)
from pyfanedit.session import Session


# ---------------------------------------------------------------------------
# helpers — install a fake Session into the client
# ---------------------------------------------------------------------------

class _FakeSession:
    def __init__(self) -> None:
        self.calls = []
        self.responses = {}  # path -> html (or list[html] for paged)

    def get(self, path, params=None, use_cache=True):
        self.calls.append(("GET", path, dict(params or {})))
        key = path
        if key in self.responses:
            v = self.responses[key]
            if isinstance(v, list):
                return v.pop(0) if v else "<html></html>"
            return v
        return "<html></html>"

    def post(self, path, data=None):
        self.calls.append(("POST", path, dict(data or {})))
        return self.responses.get(path, "<html></html>")


@pytest.fixture
def fake_client(monkeypatch):
    sess = _FakeSession()
    import pyfanedit.client as cl
    monkeypatch.setattr(cl, "Session", lambda *a, **kw: sess)
    return FaneditClient(), sess


# ---------------------------------------------------------------------------
# Synthetic HTML fragments
# ---------------------------------------------------------------------------

LISTING_CATEGORY_HTML = """
<html><body>
  <div class="jr-layout-outer">
    <div class="jrListingThumbnail">
      <img data-jr-src="https://example.com/cover.jpg" />
    </div>
    <div class="jrListingTitle"><a href="https://fanedit.org/foo-edit/">Foo Edit</a></div>
    <div class="jrOverallEditor"><span class="jrRatingValue">8.5 (3)</span></div>
    <div class="jrOverallUser"><span class="jrRatingValue">9.0 (12)</span></div>
    <span><span class="jrIconGraph"></span>1234</span>
    <div class="jrDateValue">2024-01-02</div>
    <div class="jrFieldRow">
      <div class="jrFieldLabel">Faneditor name:</div>
      <div class="jrFieldValue">Jane</div>
    </div>
    <div class="jrFieldRow">
      <div class="jrFieldLabel">Original Movie/Show Title:</div>
      <div class="jrFieldValue">Foo Movie</div>
    </div>
    <div class="jrFieldRow">
      <div class="jrFieldLabel">Fanedit Release Date:</div>
      <div class="jrFieldValue">2023-05-01</div>
    </div>
    <div class="jrFieldRow">
      <div class="jrFieldLabel">Fanedit Running Time:</div>
      <div class="jrFieldValue">1h 45m</div>
    </div>
    <div class="jrFieldRow">
      <div class="jrFieldLabel">Synopsis:</div>
      <div class="jrFieldValue">A synopsis.</div>
    </div>
    <div class="jrFieldRow">
      <div class="jrFieldLabel">Franchise:</div>
      <div class="jrFieldValue">Foo Franchise</div>
    </div>
    <div class="jrFieldRow">
      <div class="jrFieldLabel">Fanedit Type:</div>
      <div class="jrFieldValue">extended</div>
    </div>
  </div>
  <div class="jrPagination">
    <span class="jrPageCurrent">1</span>
    <a href="?pg=2">2</a>
  </div>
</body></html>
"""

LISTING_SEARCH_HTML = """
<html><body>
  <div class="jrRow jrDataListHeader">header</div>
  <div class="jrRow">
    <div class="jrListingTitle"><a href="https://fanedit.org/bar-edit/">Bar Edit</a></div>
    <div class="jrListingCategory">fanfix</div>
  </div>
  <div class="jrRow">
    <!-- skip: no title -->
  </div>
  <div class="jrRow">
    <div class="jrListingTitle"><span>no anchor</span></div>
  </div>
</body></html>
"""

DETAIL_HTML = """
<html><body class="postid-4242">
  <h1 class="contentheading">Detail Title</h1>
  <img class="jrMediaPhoto" data-jr-src="https://example.com/c.jpg" />
  <a href="https://imdb.com/tt0076759">imdb</a>
  <div class="jrOverallEditor"><span class="jrRatingValue">7.5 (2)</span></div>
  <div class="jrOverallUser"><span class="jrRatingValue">8.0 (10)</span></div>

  <div class="jrFieldRow"><div class="jrFieldLabel">Faneditor Name:</div><div class="jrFieldValue">Alice</div></div>
  <div class="jrFieldRow"><div class="jrFieldLabel">Original Movie/Show Title:</div><div class="jrFieldValue">Source Film</div></div>
  <div class="jrFieldRow"><div class="jrFieldLabel">Fanedit Type:</div><div class="jrFieldValue">extended</div></div>
  <div class="jrFieldRow"><div class="jrFieldLabel">Fanedit Release Date:</div><div class="jrFieldValue">2024-02-03</div></div>
  <div class="jrFieldRow"><div class="jrFieldLabel">Fanedit Running Time:</div><div class="jrFieldValue">2h</div></div>
  <div class="jrFieldRow"><div class="jrFieldLabel">Available in:</div><div class="jrFieldValue">HD Surround Sound</div></div>
  <div class="jrFieldRow"><div class="jrFieldLabel">Release Information:</div><div class="jrFieldValue">From BD-50 master</div></div>
  <div class="jrFieldRow"><div class="jrFieldLabel">Synopsis:</div><div class="jrFieldValue">syn</div></div>
  <div class="jrFieldRow"><div class="jrFieldLabel">Intention:</div><div class="jrFieldValue">recut</div></div>
  <div class="jrFieldRow"><div class="jrFieldLabel">Genre:</div><div class="jrFieldValue"><a>Action</a><a>Drama</a></div></div>
  <div class="jrFieldRow"><div class="jrFieldLabel">Franchise:</div><div class="jrFieldValue"><a>Foo</a></div></div>
  <div class="jrFieldRow"><div class="jrFieldLabel">Custom Unknown:</div><div class="jrFieldValue">somevalue</div></div>
  <!-- duplicate label is deduplicated -->
  <div class="jrFieldRow"><div class="jrFieldLabel">Faneditor Name:</div><div class="jrFieldValue">DuplicateIgnored</div></div>

  <div class="jrEditorReviewsContainer">
    <div class="jrReviewLayout">
      <!-- summary placeholder skipped -->
    </div>
    <div class="jrReviewLayout">
      <div class="jrReviewLayoutLeft">
        <span itemprop="name">Reviewer1</span>
        <a itemprop="url" href="/r1/">profile</a>
        <span class="jrReviewerRank">Top Reviewer</span>
        <span class="jrReviewerReviews">12 reviews</span>
      </div>
      <time class="jrReviewCreated" datetime="2024-01-01">Jan 1</time>
      <div class="jrRatingTable">
        <div class="fwd-table-row">
          <div class="jrRatingLabel">Overall rating</div>
          <div class="jrRatingValue">9.0</div>
        </div>
        <div class="fwd-table-row">
          <div class="jrRatingLabel">Audio/Video Quality</div>
          <div class="jrRatingValue">not-a-number</div>
        </div>
        <div class="fwd-table-row">
          <div class="jrRatingLabel">Narrative</div>
          <div class="jrRatingValue">8.5</div>
        </div>
        <div class="fwd-table-row">
          <div class="jrRatingLabel">unknown row</div>
        </div>
      </div>
      <div class="jrReviewComment">Body text here.</div>
      <div class="jrReviewActions">
        <a class="jrDiscussReview" href="/discuss/1">d</a>
        <div class="jr-review-vote">
          <div class="jrVoteYes"><span class="count-text">5</span></div>
          <div class="jrVoteNo"><span class="count-text">notnum</span></div>
        </div>
      </div>
    </div>
  </div>
  <div class="jrUserReviewsContainer">
    <div class="jrReviewLayout">
      <div class="jrReviewLayoutLeft">
        <span itemprop="name">UserA</span>
      </div>
    </div>
  </div>
</body></html>
"""

REVIEWER_RANK_HTML = """
<html><body>
  <div class="jrRow jrDataListHeader">hdr</div>
  <div class="jrRow">
    <div class="jrCenterAlign" id="user-100">7</div>
    <div class="jrReviewAuthor"><a href="/m/alice">Alice</a></div>
    <div class="jrRankContent">
      <a href="/my-reviews/100/">123 reviews</a>
      Helpful votes: 80 (90.5%)
    </div>
  </div>
  <div class="jrRow">
    <!-- no rank_col, skip -->
  </div>
  <div class="jrRow">
    <div class="jrCenterAlign" id="not-a-user">x</div>
  </div>
  <div class="jrRow">
    <div class="jrCenterAlign" id="user-200">notint</div>
  </div>
  <div class="jrRow">
    <div class="jrCenterAlign" id="user-300">3</div>
    <!-- no jrReviewAuthor → skip -->
  </div>
  <div class="jrRow">
    <div class="jrCenterAlign" id="user-400">4</div>
    <div class="jrReviewAuthor"><a href="/m/d">D</a></div>
    <!-- no rankcontent → fallback url -->
  </div>
  <div class="jrRow">
    <div class="jrCenterAlign" id="user-500">5</div>
    <div class="jrReviewAuthor"><a href="/m/e">E</a></div>
    <div class="jrRankContent">no anchor here</div>
  </div>
  <div class="jrPagination">
    <span class="jrPageCurrent">1</span>
    <a href="?pg=2">2</a>
  </div>
</body></html>
"""

USER_REVIEWS_HTML = """
<html><body>
  <div class="jrReviewListLayout">
    <div class="jrListingTitle"><a href="/foo/">Foo</a></div>
    <div class="jrListingCategory">fanfix</div>
    <span class="jrReviewCreated" datetime="2024-04-01">Apr 1</span>
    <div class="jrRatingTable">
      <div class="fwd-table-row">
        <div class="jrRatingLabel">Overall rating</div>
        <div class="jrRatingValue">9.0</div>
      </div>
    </div>
    <a class="jrButton" href="/discussions/1/">Comments (3)</a>
  </div>
  <div class="jrReviewListLayout">
    <!-- no listing title — skipped -->
  </div>
  <div class="jrReviewListLayout">
    <div class="jrListingTitle"><span>no anchor</span></div>
  </div>
  <div class="jrReviewListLayout">
    <div class="jrListingTitle"><a href="/bar/">Bar</a></div>
  </div>
  <div class="jrPagination">
    <span class="jrPageCurrent">1</span>
    <a href="?pg=2">2</a>
  </div>
</body></html>
"""

NEWS_LISTING_HTML = """
<html><body>
  <div class="newsCard-grid-item js-threadListItem-99">
    <div class="newsCard-grid-title"><a href="/forums/article.99/">News Title</a></div>
    <img class="newsCard-grid-image-link" src="/thumb.jpg" />
    <a data-user-id="42"><img alt="Bob"/></a>
    <time datetime="2024-05-01T00:00:00Z"></time>
    <li class="newsCard-date">Reading time2 min read</li>
  </div>
  <div class="newsCard-grid-item js-threadListItem-100">
    <!-- no title -> skip -->
  </div>
  <div class="newsCard-grid-item js-threadListItem-101">
    <div class="newsCard-grid-title"><span>no anchor</span></div>
  </div>
  <div class="newsCard-grid-item">
    <!-- no thread id -> skip -->
    <div class="newsCard-grid-title"><a href="/x">x</a></div>
  </div>
  <div class="newsCard-grid-item js-threadListItem-200">
    <div class="newsCard-grid-title"><a href="https://example.org/abs/">Absolute</a></div>
    <a data-user-id="not-an-int"><img/></a>
    <li class="newsCard-date">no read marker</li>
  </div>
</body></html>
"""

NEWS_ARTICLE_HTML = """
<html><body>
  <article class="newsBody-main" data-lb-id="news-77"></article>
  <h1 class="p-title-value">Article Title</h1>
  <img class="newsView-newsThumbnail-header" src="/thumb.jpg"/>
  <div class="p-description">
    <a data-user-id="9">Author</a>
    <time datetime="2024-06-01"></time>
    <li>3 min read</li>
    <li>not relevant</li>
  </div>
  <div class="pairs--justified">Views 1,234</div>
  <div class="pairs--justified">Views notnum</div>
  <nav class="p-breadcrumbs"><a>Home</a><a>News</a></nav>
  <div class="bbWrapper">
    body content
    <a href="https://fanedit.org/some-edit/">edit</a>
    <a href="https://fanedit.org/forums/x/">forum</a>
    <a href="https://example.org/other">other</a>
    <a href="https://fanedit.org/some-edit/">dup</a>
  </div>
</body></html>
"""

NEWS_ARTICLE_MIN_HTML = """
<html><body>
  <h1>Plain Title</h1>
</body></html>
"""


# ---------------------------------------------------------------------------
# Parser tests — direct
# ---------------------------------------------------------------------------

def test_parse_listing_category():
    items, nxt = parse_listing_page(LISTING_CATEGORY_HTML)
    assert len(items) == 1
    it = items[0]
    assert it.title == "Foo Edit"
    assert it.cover_url == "https://example.com/cover.jpg"
    assert it.editor_rating == 8.5
    assert it.user_rating == 9.0
    assert it.user_rating_count == 12
    assert it.views == 1234
    assert it.faneditor == "Jane"
    assert it.fanedit_type == "extended"
    assert nxt == "?pg=2"


def test_parse_listing_search_layout():
    items, _ = parse_listing_page(LISTING_SEARCH_HTML)
    assert len(items) == 1
    assert items[0].title == "Bar Edit"
    assert items[0].fanedit_type == "fanfix"


def test_parse_listing_empty():
    items, nxt = parse_listing_page("<html></html>")
    assert items == []
    assert nxt is None


def test_parse_detail():
    detail = parse_detail_page(DETAIL_HTML, "https://fanedit.org/detail-slug/")
    assert detail.fanedit_id == 4242
    assert detail.slug == "detail-slug"
    assert detail.imdb_id == "tt0076759"
    assert detail.cover_url == "https://example.com/c.jpg"
    assert detail.faneditor == "Alice"
    assert detail.genre == ["Action", "Drama"]
    assert detail.franchise == ["Foo"]
    assert detail.extra_fields == {"custom unknown:": "somevalue"}
    assert detail.editor_rating == 7.5
    assert detail.user_rating == 8.0
    assert detail.user_rating_count == 10
    assert len(detail.editor_reviews) == 1
    rev = detail.editor_reviews[0]
    assert rev.reviewer == "Reviewer1"
    assert rev.body == "Body text here."
    assert rev.helpful_yes == 5
    assert rev.ratings.overall == 9.0
    assert rev.ratings.narrative == 8.5
    # bad value silently dropped
    assert rev.ratings.audio_video_quality is None


def test_parse_detail_data_uri_cover_dropped():
    html = '<html><body><img class="jrMediaPhoto" src="data:image/png;base64,abc"/></body></html>'
    d = parse_detail_page(html, "https://fanedit.org/x/")
    assert d.cover_url is None


def test_parse_detail_no_jrmedia():
    html = "<html><body></body></html>"
    d = parse_detail_page(html, "https://fanedit.org/x/")
    assert d.cover_url is None
    assert d.imdb_id is None
    assert d.fanedit_id is None


def test_parse_reviewer_rank():
    entries, nxt = parse_reviewer_rank_page(REVIEWER_RANK_HTML)
    assert nxt == "?pg=2"
    by_id = {e.user_id: e for e in entries}
    assert 100 in by_id
    a = by_id[100]
    assert a.review_count == 123
    assert a.helpful_yes == 80
    assert a.helpful_pct == 90.5
    # rows with broken data are skipped
    assert 200 not in by_id  # rank not int
    assert 300 not in by_id  # no author
    # fallback reviews_url for missing rank content / no anchor
    assert by_id[400].reviews_url == "https://fanedit.org/my-reviews/400/"
    assert by_id[500].reviews_url == "https://fanedit.org/my-reviews/500/"


def test_parse_user_reviews():
    items, nxt = parse_user_reviews_page(USER_REVIEWS_HTML)
    assert nxt == "?pg=2"
    assert len(items) == 2
    a = items[0]
    assert a.fanedit_url == "https://fanedit.org/foo/"
    assert a.fanedit_type == "fanfix"
    assert a.date == "2024-04-01"
    assert a.ratings.overall == 9.0
    assert a.discussion_url == "/discussions/1/"
    assert a.comment_count == 3


def test_parse_news_listing():
    items = parse_news_listing(NEWS_LISTING_HTML)
    ids = [i.thread_id for i in items]
    assert 99 in ids and 200 in ids
    by_id = {i.thread_id: i for i in items}
    a = by_id[99]
    assert a.title == "News Title"
    assert a.url.startswith("https://fanedit.org/")
    assert a.author == "Bob"
    assert a.author_user_id == 42
    assert a.published_at == "2024-05-01T00:00:00Z"
    assert a.reading_time == "2 min read"
    # absolute URL kept; bad user-id silently dropped
    assert by_id[200].url == "https://example.org/abs/"
    assert by_id[200].author_user_id is None


def test_parse_news_article_full():
    art = parse_news_article(NEWS_ARTICLE_HTML, "https://fanedit.org/forums/article.77/")
    assert art.thread_id == 77
    assert art.title == "Article Title"
    assert art.thumbnail_url == "/thumb.jpg"
    assert art.author == "Author"
    assert art.author_user_id == 9
    assert art.published_at == "2024-06-01"
    assert art.reading_time == "3 min read"
    assert art.views == 1234
    assert art.category == "News"
    assert "body content" in (art.body_text or "")
    assert "https://fanedit.org/some-edit/" in art.mentioned_fanedit_urls
    assert all("/forums/" not in u for u in art.mentioned_fanedit_urls)
    # no duplicates
    assert art.mentioned_fanedit_urls.count("https://fanedit.org/some-edit/") == 1


def test_parse_news_article_minimal():
    art = parse_news_article(NEWS_ARTICLE_MIN_HTML, "https://fanedit.org/x/")
    assert art.thread_id == 0
    assert art.title == "Plain Title"
    assert art.body_text is None


# ---------------------------------------------------------------------------
# Client wrappers — verify URL/params + parsing round-trip
# ---------------------------------------------------------------------------

def test_client_search_paged(fake_client):
    cl, sess = fake_client
    sess.responses["fanedit-search/search-results/"] = LISTING_SEARCH_HTML
    items, _ = cl.search("foo", page=2)
    assert sess.calls[0][2]["pg"] == 2
    assert sess.calls[0][2]["keywords"] == "foo"
    assert items


def test_client_get_by_tag_paged(fake_client):
    cl, sess = fake_client
    sess.responses["fanedit-search/tag/franchise/star-wars/"] = LISTING_CATEGORY_HTML
    items, _ = cl.get_by_tag("franchise", "star-wars", page=3)
    assert sess.calls[0][1] == "fanedit-search/tag/franchise/star-wars/"
    assert sess.calls[0][2]["pg"] == 3
    assert items


def test_client_iter_category(fake_client):
    cl, sess = fake_client
    p1 = LISTING_CATEGORY_HTML  # has a next-page link
    p2 = """<html><body><div class="jr-layout-outer">
      <div class="jrListingTitle"><a href="/x/">x</a></div>
    </div></body></html>"""
    sess.responses[CATEGORIES["fanfix"]] = [p1, p2]
    out = list(cl.iter_category("fanfix", max_pages=2))
    assert len(out) == 2


def test_client_iter_search_stops_on_no_next(fake_client):
    cl, sess = fake_client
    p = """<html><body><div class="jr-layout-outer">
      <div class="jrListingTitle"><a href="/y/">y</a></div>
    </div></body></html>"""
    sess.responses["fanedit-search/search-results/"] = p
    out = list(cl.iter_search("k"))
    assert len(out) == 1


def test_client_iter_by_tag(fake_client):
    cl, sess = fake_client
    p = """<html><body><div class="jr-layout-outer">
      <div class="jrListingTitle"><a href="/z/">z</a></div>
    </div></body></html>"""
    sess.responses["fanedit-search/tag/franchise/foo/"] = p
    out = list(cl.iter_by_tag("franchise", "foo", max_pages=1))
    assert len(out) == 1


def test_client_top_trusted_and_award(fake_client):
    cl, sess = fake_client
    sess.responses["top-trusted-reviewer-rated-fanedits/"] = LISTING_CATEGORY_HTML
    items, _ = cl.get_top_trusted_rated(page=2)
    assert sess.calls[-1][2]["pg"] == 2
    assert items
    sess.responses["fanedit-search/tag/award/fanedit-of-the-month/"] = LISTING_CATEGORY_HTML
    items, _ = cl.get_award_winners(page=2)
    assert items


def test_client_search_by_original_title(fake_client):
    cl, sess = fake_client
    sess.responses["fanedit-search/search-results/"] = LISTING_CATEGORY_HTML
    out = cl.search_by_original_title("Foo Movie")
    assert len(out) == 1
    out2 = cl.search_by_original_title("nonmatch")
    assert out2 == []


def test_client_get_detail_and_by_slug(fake_client):
    cl, sess = fake_client
    sess.responses["https://fanedit.org/foo-slug/"] = DETAIL_HTML
    d = cl.get_detail("foo-slug")
    assert isinstance(d, FaneditDetail)
    d2 = cl.get_detail_by_slug("foo-slug")
    assert d2.fanedit_id == 4242
    # full URL form
    sess.responses["https://fanedit.org/abs-slug/"] = DETAIL_HTML
    d3 = cl.get_detail("https://fanedit.org/abs-slug/")
    assert d3.title


def test_client_iter_reviewer_rank(fake_client):
    cl, sess = fake_client
    sess.responses["reviewer-rank/"] = REVIEWER_RANK_HTML
    out = list(cl.iter_reviewer_rank(max_pages=1))
    assert any(isinstance(e, ReviewerEntry) for e in out)


def test_client_user_reviews_paged(fake_client):
    cl, sess = fake_client
    sess.responses["my-reviews/42/"] = USER_REVIEWS_HTML
    items, _ = cl.get_user_reviews(42, page=2, order="rating")
    assert sess.calls[0][2]["pg"] == 2
    assert sess.calls[0][2]["order"] == "rating"
    assert items
    out = list(cl.iter_user_reviews(42, max_pages=1))
    assert all(isinstance(r, UserReviewEntry) for r in out)


def test_client_latest_trusted_reviews(fake_client):
    cl, sess = fake_client
    sess.responses["latest-trusted-reviewer-reviews/"] = LISTING_CATEGORY_HTML
    items, _ = cl.get_latest_trusted_reviews(page=2)
    assert sess.calls[0][2]["pg"] == 2
    assert items


def test_client_get_news_article(fake_client):
    cl, sess = fake_client
    sess.responses["https://fanedit.org/forums/article.77/"] = NEWS_ARTICLE_HTML
    art = cl.get_news_article("/forums/article.77/")
    assert isinstance(art, NewsArticle)
    assert art.thread_id == 77
    sess.responses["https://fanedit.org/forums/article.78/"] = NEWS_ARTICLE_HTML
    art2 = cl.get_news_article("https://fanedit.org/forums/article.78/")
    assert art2.title == "Article Title"


# ---------------------------------------------------------------------------
# Converter — extra branches
# ---------------------------------------------------------------------------

def test_runtime_seconds_variants():
    assert _parse_runtime_seconds(None) is None
    assert _parse_runtime_seconds("") is None
    assert _parse_runtime_seconds("105 min") == 6300
    assert _parse_runtime_seconds("1h 30m") == 5400
    assert _parse_runtime_seconds("90") == 5400
    assert _parse_runtime_seconds("nope") is None


def test_available_in_resolution_hdr_audio():
    assert _parse_available_in("4k Dolby Vision 7.1") == ("2160p", "Dolby Vision", "7.1")
    assert _parse_available_in("1440p HDR10+ stereo") == ("1440p", "HDR10+", "stereo")
    assert _parse_available_in("1080p HDR10 mono") == ("1080p", "HDR10", "mono")
    assert _parse_available_in("720p HDR 5.1") == ("720p", "HDR", "5.1")
    assert _parse_available_in("SD") == ("480p", "", "")
    assert _parse_available_in("") == ("", "", "")
    assert _parse_available_in("strange") == ("", "", "")


def test_source_format_patterns():
    assert _parse_source_format("BD-100 master") == "BD-100"
    assert _parse_source_format("From BD-66") == "BD-66"
    assert _parse_source_format("BD-50") == "BD-50"
    assert _parse_source_format("BD-25") == "BD-25"
    assert _parse_source_format("UHD Blu-ray") == "UHD Blu-ray"
    assert _parse_source_format("Blu-ray master") == "Blu-ray"
    assert _parse_source_format("Web-DL release") == "WEB-DL"
    assert _parse_source_format("Webrip") == "WEBRip"
    assert _parse_source_format("HDTV") == "HDTV"
    assert _parse_source_format("DVD") == "DVD"
    assert _parse_source_format("VHS rip") == "VHS"
    assert _parse_source_format("LaserDisc") == "LaserDisc"
    assert _parse_source_format("") == ""
    assert _parse_source_format("nothing") == ""


def test_extract_edition_variants():
    assert _extract_edition("") == ""
    assert _extract_edition("NoMarkers") == ""
    assert _extract_edition("Foo: The Director's Cut") == "The Director's Cut"


def test_fanedit_to_release_summary_with_release_date():
    s = FaneditSummary(
        title="X", url="u", fanedit_type="fanfix",
        faneditor="ed", release_date="2020-01-01", running_time="100 min",
    )
    rel = fanedit_to_release(s)
    assert rel.work.year == 2020


def test_fanedit_to_release_invalid_release_date():
    s = FaneditSummary(
        title="X", url="u", fanedit_type="fanfix", release_date="bogus",
    )
    rel = fanedit_to_release(s)
    assert rel.work.year is None


def test_fanedit_to_release_detail_invalid_date():
    d = FaneditDetail(
        title="X", url="u", fanedit_type="fanfix",
        fanedit_release_date="not-a-date",
    )
    rel = fanedit_to_release(d)
    # fallback path drops release_date if validator rejects
    assert rel.work.year is None


# ---------------------------------------------------------------------------
# Session — mock curl_cffi at the response level
# ---------------------------------------------------------------------------

def _fake_response(text="<html>ok</html>"):
    r = MagicMock()
    r.text = text
    r.raise_for_status = MagicMock()
    return r


class _FakeTransport:
    def __init__(self, *responses):
        self._responses = list(responses) or [_fake_response()]
        self.get_calls = []
        self.post_calls = []

    def _next(self):
        if len(self._responses) > 1:
            return self._responses.pop(0)
        return self._responses[0]

    def get(self, url, params=None, headers=None):
        self.get_calls.append((url, params))
        return self._next()

    def post(self, url, data=None, headers=None):
        self.post_calls.append((url, data))
        return self._next()


def _factory(transport):
    def make(**kwargs):
        return transport
    return make


def test_session_get_caches_and_replays():
    t = _FakeTransport(_fake_response("<html>1</html>"))
    s = Session(cache_ttl=60.0, session_factory=_factory(t))
    first = s.get("foo/", params={"a": "1"})
    second = s.get("foo/", params={"a": "1"})
    assert first == second == "<html>1</html>"
    assert len(t.get_calls) == 1  # cached


def test_session_get_no_cache():
    t = _FakeTransport(_fake_response("a"), _fake_response("b"))
    s = Session(session_factory=_factory(t))
    assert s.get("p", use_cache=False) == "a"
    assert s.get("p", use_cache=False) == "b"


def test_session_cache_ttl_expiry():
    t = _FakeTransport(_fake_response("a"), _fake_response("b"))
    s = Session(cache_ttl=0.0001, session_factory=_factory(t))
    assert s.get("p") == "a"
    import time as _t
    _t.sleep(0.01)
    assert s.get("p") == "b"


def test_session_cache_eviction():
    t = _FakeTransport(_fake_response("x"))
    s = Session(cache_size=2, session_factory=_factory(t))
    s.get("a")
    s.get("b")
    s.get("c")
    assert len(s._cache) == 2


def test_session_post():
    t = _FakeTransport(_fake_response("posted"))
    s = Session(session_factory=_factory(t))
    assert s.post("x/", data={"k": "v"}) == "posted"
    assert s.post("https://fanedit.org/y/", data={}) == "posted"


def test_session_get_absolute_url_no_cache_size():
    t = _FakeTransport(_fake_response("z"))
    s = Session(cache_size=0, session_factory=_factory(t))
    assert s.get("https://fanedit.org/abs", params=None) == "z"


def test_session_factory_typeerror_fallback():
    """Factory that rejects 'impersonate' kwarg falls back to bare call."""
    calls = []

    def factory(**kwargs):
        if kwargs:
            raise TypeError("no kwargs")
        calls.append("bare")
        return _FakeTransport(_fake_response("ok"))

    s = Session(session_factory=factory)
    assert calls == ["bare"]
    assert s.get("p") == "ok"


def test_session_default_factory_returns_session(monkeypatch):
    """Auto-detect path: just verify it constructs without raising."""
    monkeypatch.setenv("PYFANEDIT_TRANSPORT", "curl_cffi")
    s = Session()
    assert s is not None


def test_session_select_transport_env(monkeypatch):
    from pyfanedit.session import _select_transport
    monkeypatch.setenv("PYFANEDIT_TRANSPORT", "requests")
    assert _select_transport() == "requests"
    monkeypatch.setenv("PYFANEDIT_TRANSPORT", "curl-cffi")
    assert _select_transport() == "curl_cffi"
    monkeypatch.setenv("PYFANEDIT_TRANSPORT", "")
    # auto-detect: should return one of the two
    assert _select_transport() in ("curl_cffi", "requests")


def test_session_default_factory_requests_path(monkeypatch):
    """Force the plain-requests fallback branch."""
    monkeypatch.setenv("PYFANEDIT_TRANSPORT", "requests")
    from pyfanedit.session import _default_session_factory
    with pytest.warns(RuntimeWarning):
        sess = _default_session_factory()
    assert sess is not None


def test_make_default_session_handles_exception(monkeypatch):
    from pyfanedit import session as sess_mod
    # If Session raises, _make_default_session swallows it and returns None.
    monkeypatch.setattr(
        sess_mod, "Session",
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    assert sess_mod._make_default_session() is None


# ---------------------------------------------------------------------------
# __init__ smoke
# ---------------------------------------------------------------------------

def test_public_api():
    for name in (
        "FaneditClient", "FaneditSummary", "FaneditDetail",
        "ReviewerEntry", "UserReviewEntry", "NewsArticle",
        "Review", "ReviewRatings", "CATEGORIES", "fanedit_to_release",
        "__version__",
    ):
        assert hasattr(pyfanedit, name)
