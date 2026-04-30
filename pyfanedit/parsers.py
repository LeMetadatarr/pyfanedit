"""HTML parsers for fanedit.org pages."""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup, Tag

from pyfanedit.models import FaneditDetail, FaneditSummary, Review, ReviewRatings

# Map of raw label text → FaneditDetail field name
_DETAIL_FIELD_MAP = {
    "faneditor name:": "faneditor",
    "original movie/show title:": "original_title",
    "fanedit type:": "fanedit_type",
    "original release date:": "original_release_date",
    "original running time:": "original_running_time",
    "fanedit release date:": "fanedit_release_date",
    "fanedit running time:": "fanedit_running_time",
    "time cut:": "time_cut",
    "time added:": "time_added",
    "subtitles available:": "subtitles",
    "available in:": "available_in",
    "synopsis:": "synopsis",
    "additional notes:": "additional_notes",
    "special thanks:": "special_thanks",
    "release information:": "release_information",
    "cuts and additions:": "cuts_and_additions",
    "intention:": "intention",
    "awards:": "awards",
}

_SUMMARY_FIELD_MAP = {
    "faneditor name:": "faneditor",
    "original movie/show title:": "original_title",
    "fanedit type:": "fanedit_type",
    "fanedit release date:": "release_date",
    "fanedit running time:": "running_time",
    "synopsis:": "synopsis",
    "franchise:": "franchise",
}

_REVIEW_RATING_MAP = {
    "overall rating": "overall",
    "audio/video quality": "audio_video_quality",
    "audio editing": "audio_editing",
    "visual editing": "visual_editing",
    "narrative": "narrative",
    "enjoyment": "enjoyment",
}


def _parse_overall_rating(el: Optional[Tag]) -> Tuple[Optional[float], Optional[int]]:
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
    return None if src.startswith("data:") else (src or None)


def _imdb_id(soup: BeautifulSoup) -> Optional[str]:
    for a in soup.find_all("a", href=True):
        m = re.search(r"/(tt\d+)", a["href"])
        if m:
            return m.group(1)
    return None


def _wp_post_id(soup: BeautifulSoup) -> Optional[int]:
    body = soup.find("body")
    if body:
        for cls in body.get("class", []):
            m = re.match(r"postid-(\d+)", cls)
            if m:
                return int(m.group(1))
    return None


def _slug_from_url(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def _parse_review_ratings(rating_table: Tag) -> ReviewRatings:
    kwargs: dict = {}
    for row in rating_table.find_all(class_="fwd-table-row"):
        cells = row.find_all(class_=["jrRatingLabel", "jrRatingValue"])
        if len(cells) < 2:
            continue
        label = cells[0].get_text(strip=True).lower()
        val_text = cells[-1].get_text(strip=True)
        field = _REVIEW_RATING_MAP.get(label)
        if field:
            try:
                kwargs[field] = float(val_text)
            except ValueError:
                pass
    return ReviewRatings(**kwargs)


def _parse_review(review_el: Tag) -> Review:
    # reviewer identity (left panel)
    reviewer = reviewer_url = reviewer_rank = None
    reviewer_review_count = None
    left = review_el.find(class_="jrReviewLayoutLeft")
    if left:
        author_el = left.find(itemprop="name")
        if author_el:
            reviewer = author_el.get_text(strip=True)
        author_url_el = left.find(itemprop="url")
        if author_url_el:
            reviewer_url = author_url_el.get("href")
        rank_el = left.find(class_="jrReviewerRank")
        if rank_el:
            reviewer_rank = rank_el.get_text(strip=True)
        rev_count_el = left.find(class_="jrReviewerReviews")
        if rev_count_el:
            m = re.search(r"(\d+)", rev_count_el.get_text())
            if m:
                reviewer_review_count = int(m.group(1))

    # date
    date = None
    time_el = review_el.find("time", class_="jrReviewCreated")
    if time_el:
        date = time_el.get("datetime") or time_el.get_text(strip=True)

    # ratings
    rating_table = review_el.find(class_="jrRatingTable")
    ratings = _parse_review_ratings(rating_table) if rating_table else ReviewRatings()

    # body text
    body = None
    comment_el = review_el.find(class_="jrReviewComment")
    if comment_el:
        body = comment_el.get_text(" ", strip=True)

    # discussion / helpful
    discussion_url = None
    helpful_yes = helpful_no = None
    footer = review_el.find(class_="jrReviewActions")
    if footer:
        discuss_a = footer.find(class_="jrDiscussReview")
        if discuss_a:
            discussion_url = discuss_a.get("href")
        vote_el = footer.find(class_="jr-review-vote")
        if vote_el:
            yes_el = vote_el.find(class_="jrVoteYes")
            no_el = vote_el.find(class_="jrVoteNo")
            if yes_el:
                try:
                    helpful_yes = int(yes_el.find(class_="count-text").get_text(strip=True))
                except (AttributeError, ValueError):
                    pass
            if no_el:
                try:
                    helpful_no = int(no_el.find(class_="count-text").get_text(strip=True))
                except (AttributeError, ValueError):
                    pass

    return Review(
        reviewer=reviewer,
        reviewer_url=reviewer_url,
        reviewer_rank=reviewer_rank,
        reviewer_review_count=reviewer_review_count,
        date=date,
        ratings=ratings,
        body=body,
        discussion_url=discussion_url,
        helpful_yes=helpful_yes,
        helpful_no=helpful_no,
    )


def _parse_reviews(soup: BeautifulSoup, container_class: str) -> List[Review]:
    section = soup.find(class_=container_class)
    if section is None:
        return []
    reviews = []
    for el in section.find_all(class_="jrReviewLayout"):
        # skip the summary placeholder (no jrReviewLayoutLeft = no real reviewer)
        if el.find(class_="jrReviewLayoutLeft") is None:
            continue
        reviews.append(_parse_review(el))
    return reviews


def _parse_outer(outer: Tag) -> Optional[FaneditSummary]:
    title_el = outer.find(class_="jrListingTitle")
    if title_el is None:
        return None
    a = title_el.find("a")
    if a is None:
        return None

    title = a.get_text(strip=True)
    url = a["href"]
    slug = _slug_from_url(url)

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
    editor_r, _ = _parse_overall_rating(outer.find(class_="jrOverallEditor"))
    user_r, user_cnt = _parse_overall_rating(outer.find(class_="jrOverallUser"))

    # views
    views: Optional[int] = None
    for span in outer.find_all("span"):
        if span.find(class_="jrIconGraph"):
            try:
                views = int(span.get_text(strip=True))
            except ValueError:
                pass

    # date
    updated: Optional[str] = None
    date_el = outer.find(class_="jrDateValue")
    if date_el:
        updated = date_el.get_text(strip=True)

    # fanedit type from jrListingCategory (search results layout)
    fanedit_type: Optional[str] = None
    cat_el = outer.find(class_="jrListingCategory")
    if cat_el:
        fanedit_type = cat_el.get_text(strip=True)

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

    if fanedit_type and "fanedit_type" not in kwargs:
        kwargs["fanedit_type"] = fanedit_type

    return FaneditSummary(
        slug=slug,
        title=title,
        url=url,
        cover_url=cover_url,
        editor_rating=editor_r,
        user_rating=user_r,
        user_rating_count=user_cnt,
        views=views,
        updated=updated,
        **kwargs,
    )


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
        item = _parse_outer(outer)
        if item:
            items.append(item)

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
    title = title_el.get_text(strip=True) if title_el else _slug_from_url(url)

    fanedit_id = _wp_post_id(soup)
    slug = _slug_from_url(url)
    cover_url = _cover_url(soup)
    imdb_id = _imdb_id(soup)

    # ratings
    editor_r, _ = _parse_overall_rating(soup.find(class_="jrOverallEditor"))
    user_r, user_cnt = _parse_overall_rating(soup.find(class_="jrOverallUser"))

    # fields — deduplicated by label
    seen: dict = {}
    for row in soup.find_all(class_="jrFieldRow"):
        lbl = row.find(class_="jrFieldLabel")
        val = row.find(class_="jrFieldValue")
        if lbl and val:
            key = lbl.get_text(strip=True).lower()
            if key not in seen:
                seen[key] = val

    known: dict = {}
    extra: dict = {}
    for raw_key, val_el in seen.items():
        mapped = _DETAIL_FIELD_MAP.get(raw_key)
        text = val_el.get_text(" ", strip=True)
        if mapped:
            known[mapped] = text
        elif raw_key == "genre:":
            known["genre"] = [a.get_text(strip=True) for a in val_el.find_all("a")] or [text]
        elif raw_key == "franchise:":
            known["franchise"] = [a.get_text(strip=True) for a in val_el.find_all("a")] or [text]
        else:
            extra[raw_key] = text

    editor_reviews = _parse_reviews(soup, "jrEditorReviewsContainer")
    user_reviews = _parse_reviews(soup, "jrUserReviewsContainer")

    return FaneditDetail(
        fanedit_id=fanedit_id,
        slug=slug,
        title=title,
        url=url,
        cover_url=cover_url,
        imdb_id=imdb_id,
        editor_rating=editor_r,
        user_rating=user_r,
        user_rating_count=user_cnt,
        editor_reviews=editor_reviews,
        user_reviews=user_reviews,
        extra_fields=extra,
        **known,
    )
