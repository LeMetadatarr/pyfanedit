"""High-level fanedit.org client."""
from __future__ import annotations

from typing import Iterator, List, Optional

from pyfanedit.models import FaneditDetail, FaneditSummary
from pyfanedit.parsers import parse_detail_page, parse_listing_page
from pyfanedit.session import Session

# Category slug → URL path
CATEGORIES = {
    "fanfix": "category/fanedit-listings/fanfix/",
    "fanmix": "category/fanedit-listings/fanmix/",
    "extended": "category/fanedit-listings/extended-edition/",
    "tv_to_movie": "category/fanedit-listings/tv-to-movie/",
    "movie_to_tv": "category/fanedit-listings/movie-to-tv/",
    "shorts": "category/fanedit-listings/shorts/",
    "special": "category/fanedit-listings/custom-special-edition/",
    "documentary": "category/fanedit-listings/documentary-review/",
    "preservation": "category/preservation-listings/",
    "unapproved": "category/unapproved-fanedits/",
}

ORDER_CHOICES = ("rdate", "date", "modified", "alpha", "rratio", "rvote")


class FaneditClient:
    """Scraping client for fanedit.org / IFDB."""

    def __init__(self, impersonate: str = "chrome120", cache_ttl: float = 300.0) -> None:
        self._s = Session(impersonate=impersonate, cache_ttl=cache_ttl)

    # ------------------------------------------------------------------
    # Category browsing
    # ------------------------------------------------------------------

    def get_category(
        self,
        category: str,
        page: int = 1,
    ) -> tuple[List[FaneditSummary], Optional[str]]:
        """Return one page of a category.

        ``category`` may be a key from ``CATEGORIES`` or a full URL path.
        Returns (items, next_page_url).
        """
        path = CATEGORIES.get(category, category)
        params = {"pg": page} if page > 1 else None
        html = self._s.get(path, params=params)
        return parse_listing_page(html)

    def iter_category(self, category: str, max_pages: int = 0) -> Iterator[FaneditSummary]:
        """Yield all fanedits in a category across pages."""
        page = 1
        while True:
            items, next_url = self.get_category(category, page=page)
            yield from items
            if not next_url or (max_pages and page >= max_pages):
                break
            page += 1

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        keywords: str,
        scope: str = "title",
        query_type: str = "all",
        order: str = "rdate",
        page: int = 1,
    ) -> tuple[List[FaneditSummary], Optional[str]]:
        """Search the IFDB.

        Args:
            keywords: search terms
            scope: "title" | "reviews"
            query_type: "all" | "any" | "exact"
            order: one of ORDER_CHOICES
            page: 1-based page number

        Returns:
            (items, next_page_url)
        """
        params: dict = {
            "query": query_type,
            "scope": scope,
            "keywords": keywords,
            "order": order,
        }
        if page > 1:
            params["pg"] = page
        html = self._s.get("fanedit-search/search-results/", params=params)
        return parse_listing_page(html)

    def iter_search(
        self,
        keywords: str,
        scope: str = "title",
        query_type: str = "all",
        order: str = "rdate",
        max_pages: int = 0,
    ) -> Iterator[FaneditSummary]:
        """Yield all search results across pages."""
        page = 1
        while True:
            items, next_url = self.search(
                keywords, scope=scope, query_type=query_type, order=order, page=page
            )
            yield from items
            if not next_url or (max_pages and page >= max_pages):
                break
            page += 1

    # ------------------------------------------------------------------
    # Tag / franchise browsing
    # ------------------------------------------------------------------

    def get_by_tag(
        self,
        tag_type: str,
        tag_value: str,
        page: int = 1,
    ) -> tuple[List[FaneditSummary], Optional[str]]:
        """Browse by a tag, e.g. get_by_tag("franchise", "star-wars").

        Common tag_type values: franchise, faneditorname, originalmovietitle,
        fanedittype, faneditreleasedate, award.
        """
        path = f"fanedit-search/tag/{tag_type}/{tag_value}/"
        params: dict = {"criteria": "2"}
        if page > 1:
            params["pg"] = page
        html = self._s.get(path, params=params)
        return parse_listing_page(html)

    def iter_by_tag(
        self, tag_type: str, tag_value: str, max_pages: int = 0
    ) -> Iterator[FaneditSummary]:
        page = 1
        while True:
            items, next_url = self.get_by_tag(tag_type, tag_value, page=page)
            yield from items
            if not next_url or (max_pages and page >= max_pages):
                break
            page += 1

    # ------------------------------------------------------------------
    # Curated lists
    # ------------------------------------------------------------------

    def get_latest(self, page: int = 1) -> tuple[List[FaneditSummary], Optional[str]]:
        html = self._s.get("latest-ifdb-fanedits/", params={"pg": page} if page > 1 else None)
        return parse_listing_page(html)

    def get_top_trusted_rated(self, page: int = 1) -> tuple[List[FaneditSummary], Optional[str]]:
        html = self._s.get("top-trusted-reviewer-rated-fanedits/", params={"pg": page} if page > 1 else None)
        return parse_listing_page(html)

    def get_top_user_rated(self, page: int = 1) -> tuple[List[FaneditSummary], Optional[str]]:
        html = self._s.get("top-user-rated-fanedits/", params={"pg": page} if page > 1 else None)
        return parse_listing_page(html)

    def get_most_popular(self, page: int = 1) -> tuple[List[FaneditSummary], Optional[str]]:
        html = self._s.get("most-popular/", params={"pg": page} if page > 1 else None)
        return parse_listing_page(html)

    def get_award_winners(self, page: int = 1) -> tuple[List[FaneditSummary], Optional[str]]:
        return self.get_by_tag("award", "fanedit-of-the-month", page=page)

    # ------------------------------------------------------------------
    # Detail
    # ------------------------------------------------------------------

    def get_detail(self, url: str) -> FaneditDetail:
        """Fetch and parse a single fanedit detail page.

        ``url`` may be a full URL or a slug like ``/star-wars-despecialized/``.
        """
        if not url.startswith("http"):
            url = "https://fanedit.org/" + url.strip("/") + "/"
        html = self._s.get(url)
        return parse_detail_page(html, url)
