"""HTML parsers for fanedit.org pages."""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup, Tag

from pyfanedit.models import FaneditDetail, FaneditSummary

# Map of raw label text → FaneditDetail field name
_DETAIL_FIELD_MAP = {
    "faneditor name:": "faneditor",
    "original movie/show title:": "original_title",
    "genre:": "genre",
    "fanedit type:": "fanedit_type",
    "original release date:": "original_release_date",
    "original running time:": "original_running_time",
    "fanedit release date:": "fanedit_release_date",
    "fanedit running time:": "fanedit_running_time",
    "subtitles available:": "subtitles",
    "available in:": "available_in",
    "synopsis:": "synopsis",
    "additional notes:": "additional_notes",
    "release information:": "release_information",
    "cuts and additions:": "cuts_and_additions",
}

_SUMMARY_FIELD_MAP = {
    "faneditor name:": "faneditor",
    "original movie/show title:": "original_title",
    "fanedit type:": "fanedit_type",
    "fanedit release date:": "release_date",
    "fanedit running time:": "running_time",
    "synopsis:": "synopsis",
}


def _parse_rating(el: Optional[Tag]) -> Tuple[Optional[float], Optional[int]]:
    if el is None:
        return None, None
    val_el = el.find(class_="jrRatingValue")
    if val_el is None:
        return None, None
    text = val_el.get_text(" ", strip=True)
    count = None
    count_m = re.search(r"\((\d+)\)", text)
    if count_m:
        count = int(count_m.group(1))
    rating_m = re.match(r"[\d.]+", text)
    rating = float(rating_m.group()) if rating_m else None
    return rating, count


def _cover_url(soup: BeautifulSoup) -> Optional[str]:
    img = soup.find(class_="jrMediaPhoto")
    if img is None:
        return None
    src = img.get("data-jr-src") or img.get("src", "")
    if src.startswith("data:"):
        return None
    return src or None


def parse_listing_page(html: str) -> Tuple[List[FaneditSummary], Optional[str]]:
    """Return (items, next_page_url) from a category/search listing page."""
    soup = BeautifulSoup(html, "html.parser")
    items: List[FaneditSummary] = []

    # Category pages use "jr-layout-outer"; search/tag pages use "jrRow"
    candidates = soup.find_all(class_="jr-layout-outer") or [
        el for el in soup.find_all(class_="jrRow")
        if "jrDataListHeader" not in (el.get("class") or [])
    ]

    for outer in candidates:
        title_el = outer.find(class_="jrListingTitle")
        if title_el is None:
            continue
        a = title_el.find("a")
        if a is None:
            continue

        title = a.get_text(strip=True)
        url = a["href"]
        listing_id = a.get("data-listing-id")

        # cover
        cover_url: Optional[str] = None
        thumb = outer.find(class_="jrListingThumbnail")
        if thumb:
            img = thumb.find("img")
            if img:
                src = img.get("data-jr-src") or img.get("src", "")
                if not src.startswith("data:"):
                    cover_url = src

        # ratings
        editor_r, _ = _parse_rating(outer.find(class_="jrOverallEditor"))
        user_r, user_cnt = _parse_rating(outer.find(class_="jrOverallUser"))

        # views
        views: Optional[int] = None
        for span in outer.find_all("span"):
            if span.find(class_="jrIconGraph"):
                try:
                    views = int(span.get_text(strip=True))
                except ValueError:
                    pass

        # updated date
        updated: Optional[str] = None
        date_el = outer.find(class_="jrDateValue")
        if date_el:
            updated = date_el.get_text(strip=True)

        # custom fields
        kwargs: dict = {}
        for row in outer.find_all(class_="jrFieldRow"):
            lbl = row.find(class_="jrFieldLabel")
            val = row.find(class_="jrFieldValue")
            if lbl and val:
                key = lbl.get_text(strip=True).lower()
                mapped = _SUMMARY_FIELD_MAP.get(key)
                if mapped:
                    kwargs[mapped] = val.get_text(" ", strip=True)

        items.append(FaneditSummary(
            listing_id=listing_id,
            title=title,
            url=url,
            cover_url=cover_url,
            editor_rating=editor_r,
            user_rating=user_r,
            user_rating_count=user_cnt,
            views=views,
            updated=updated,
            **kwargs,
        ))

    # next page
    next_url: Optional[str] = None
    pagenav = soup.find(class_="jrPagination")
    if pagenav:
        current = pagenav.find(class_="jrPageCurrent")
        if current:
            nxt = current.find_next_sibling("a")
            if nxt and nxt.get("href"):
                next_url = nxt["href"]

    return items, next_url


def parse_detail_page(html: str, url: str) -> FaneditDetail:
    """Parse a single fanedit detail page."""
    soup = BeautifulSoup(html, "html.parser")

    # title
    title_el = soup.find(class_="jrListingTitle") or soup.find("h1", class_="contentheading")
    title = title_el.get_text(strip=True) if title_el else url.rstrip("/").rsplit("/", 1)[-1]

    listing_id: Optional[str] = None
    lid_el = soup.find(attrs={"data-listing-id": True})
    if lid_el:
        listing_id = lid_el.get("data-listing-id")

    cover_url = _cover_url(soup)

    # ratings
    editor_r, _ = _parse_rating(soup.find(class_="jrOverallEditor"))
    user_r, user_cnt = _parse_rating(soup.find(class_="jrOverallUser"))

    # fields — deduplicate by collecting into a dict keyed on label
    seen: dict = {}
    for row in soup.find_all(class_="jrFieldRow"):
        lbl = row.find(class_="jrFieldLabel")
        val = row.find(class_="jrFieldValue")
        if lbl and val:
            key = lbl.get_text(strip=True).lower()
            if key not in seen:
                seen[key] = val.get_text(" ", strip=True)

    known: dict = {}
    extra: dict = {}
    for raw_key, raw_val in seen.items():
        mapped = _DETAIL_FIELD_MAP.get(raw_key)
        if mapped:
            known[mapped] = raw_val
        else:
            extra[raw_key] = raw_val

    return FaneditDetail(
        title=title,
        url=url,
        cover_url=cover_url,
        listing_id=listing_id,
        editor_rating=editor_r,
        user_rating=user_r,
        user_rating_count=user_cnt,
        extra_fields=extra,
        **known,
    )
