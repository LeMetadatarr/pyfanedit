"""HTML parsers for fanedit.org pages."""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup, Tag

from pyfanedit.models import (
    FaneditDetail, FaneditSummary, NewsArticle,
    Review, ReviewRatings, ReviewerEntry, UserReviewEntry,
)

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

    # /latest-user-reviews/ and /latest-trusted-reviewer-reviews/ use a
    # different markup: each entry is a ``jrReviewListLayout`` block whose
    # only fanedit-identifying element is an inner ``jrListingTitle``.
    if not items:
        for el in soup.find_all(class_="jrReviewListLayout"):
            title_el = el.find(class_="jrListingTitle")
            if title_el is None:
                continue
            a = title_el.find("a")
            if a is None or not a.get("href"):
                continue
            url = a["href"]
            title = a.get_text(strip=True)
            slug = _slug_from_url(url)
            cover_url: Optional[str] = None
            thumb = el.find(class_="jrListingThumbnail")
            if thumb:
                img = thumb.find("img")
                if img:
                    src = img.get("data-jr-src") or img.get("src", "")
                    if src and not src.startswith("data:"):
                        cover_url = src
            fanedit_type: Optional[str] = None
            cat_el = el.find(class_="jrListingCategory")
            if cat_el:
                fanedit_type = cat_el.get_text(strip=True)
            updated: Optional[str] = None
            date_el = el.find(class_="jrReviewCreated")
            if date_el:
                updated = date_el.get("datetime") or date_el.get_text(strip=True)
            items.append(FaneditSummary(
                slug=slug,
                title=title,
                url=url,
                cover_url=cover_url,
                fanedit_type=fanedit_type,
                updated=updated,
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


# ---------------------------------------------------------------------------
# Reviewer leaderboard
# ---------------------------------------------------------------------------

def parse_reviewer_rank_page(html: str) -> Tuple[List[ReviewerEntry], Optional[str]]:
    """Parse one page of /reviewer-rank/. Returns (entries, next_page_url)."""
    soup = BeautifulSoup(html, "html.parser")
    entries: List[ReviewerEntry] = []

    for row in soup.find_all(class_="jrRow"):
        if "jrDataListHeader" in (row.get("class") or []):
            continue

        rank_col = row.find(class_="jrCenterAlign")
        if rank_col is None:
            continue
        user_id_m = re.match(r"user-(\d+)", rank_col.get("id", ""))
        if not user_id_m:
            continue
        user_id = int(user_id_m.group(1))
        try:
            rank = int(rank_col.get_text(strip=True))
        except ValueError:
            continue

        # username + profile URL
        author_el = row.find(class_="jrReviewAuthor")
        if author_el is None:
            continue
        a = author_el.find("a")
        username = a.get_text(strip=True) if a else ""
        profile_url = a["href"] if a else ""

        # review count + helpful votes
        content = row.find(class_="jrRankContent")
        review_count = 0
        helpful_yes = None
        helpful_pct = None
        if content:
            rev_a = content.find("a")
            if rev_a:
                reviews_url = rev_a["href"]
                m = re.search(r"(\d+)", rev_a.get_text())
                if m:
                    review_count = int(m.group(1))
            else:
                reviews_url = f"https://fanedit.org/my-reviews/{user_id}/"
            text = content.get_text(" ", strip=True)
            hm = re.search(r"Helpful votes:\s*(\d+)\s*\(([0-9.]+)%\)", text)
            if hm:
                helpful_yes = int(hm.group(1))
                helpful_pct = float(hm.group(2))
        else:
            reviews_url = f"https://fanedit.org/my-reviews/{user_id}/"

        entries.append(ReviewerEntry(
            rank=rank,
            user_id=user_id,
            username=username,
            profile_url=profile_url,
            reviews_url=reviews_url,
            review_count=review_count,
            helpful_yes=helpful_yes,
            helpful_pct=helpful_pct,
        ))

    next_url: Optional[str] = None
    pagenav = soup.find(class_="jrPagination")
    if pagenav:
        current = pagenav.find(class_="jrPageCurrent")
        if current:
            nxt = current.find_next_sibling("a")
            if nxt and nxt.get("href"):
                next_url = nxt["href"]

    return entries, next_url


# ---------------------------------------------------------------------------
# Reviews by user
# ---------------------------------------------------------------------------

def parse_user_reviews_page(html: str) -> Tuple[List[UserReviewEntry], Optional[str]]:
    """Parse one page of /my-reviews/{user_id}/. Returns (reviews, next_page_url)."""
    soup = BeautifulSoup(html, "html.parser")
    reviews: List[UserReviewEntry] = []

    for el in soup.find_all(class_="jrReviewListLayout"):
        # fanedit link
        listing_title = el.find(class_="jrListingTitle")
        if listing_title is None:
            continue
        a = listing_title.find("a")
        if a is None:
            continue
        fanedit_url = a["href"]
        if not fanedit_url.startswith("http"):
            fanedit_url = "https://fanedit.org" + fanedit_url
        fanedit_title = a.get_text(strip=True)

        fanedit_type: Optional[str] = None
        cat_el = el.find(class_="jrListingCategory")
        if cat_el:
            fanedit_type = cat_el.get_text(strip=True)

        date: Optional[str] = None
        date_el = el.find(class_="jrReviewCreated")
        if date_el:
            date = date_el.get("datetime") or date_el.get_text(strip=True)

        rating_table = el.find(class_="jrRatingTable")
        ratings = _parse_review_ratings(rating_table) if rating_table else ReviewRatings()

        discussion_url: Optional[str] = None
        comment_count: Optional[int] = None
        for btn_a in el.find_all("a", class_="jrButton"):
            href = btn_a.get("href", "")
            if "/discussions/" in href:
                discussion_url = href
                m = re.search(r"Comments?\s*\((\d+)\)", btn_a.get_text())
                if m:
                    comment_count = int(m.group(1))

        reviews.append(UserReviewEntry(
            fanedit_title=fanedit_title,
            fanedit_url=fanedit_url,
            fanedit_type=fanedit_type,
            date=date,
            ratings=ratings,
            discussion_url=discussion_url,
            comment_count=comment_count,
        ))

    next_url: Optional[str] = None
    pagenav = soup.find(class_="jrPagination")
    if pagenav:
        current = pagenav.find(class_="jrPageCurrent")
        if current:
            nxt = current.find_next_sibling("a")
            if nxt and nxt.get("href"):
                next_url = nxt["href"]

    return reviews, next_url


# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------

def _thread_id_from_card(card: Tag) -> Optional[int]:
    for cls in card.get("class", []):
        m = re.match(r"js-threadListItem-(\d+)", cls)
        if m:
            return int(m.group(1))
    return None


def parse_news_listing(html: str) -> List[NewsArticle]:
    """Parse the news front page (/forums/news-publisher/)."""
    soup = BeautifulSoup(html, "html.parser")
    articles: List[NewsArticle] = []

    for card in soup.find_all(class_="newsCard-grid-item"):
        thread_id = _thread_id_from_card(card)
        if thread_id is None:
            continue

        title_el = card.find(class_="newsCard-grid-title")
        if title_el is None:
            continue
        a = title_el.find("a")
        if a is None:
            continue
        title = a.get_text(strip=True)
        href = a["href"]
        url = href if href.startswith("http") else "https://fanedit.org" + href

        thumbnail_url: Optional[str] = None
        img = card.find("img", class_="newsCard-grid-image-link")
        if img:
            thumbnail_url = img.get("src")

        author: Optional[str] = None
        author_user_id: Optional[int] = None
        avatar_a = card.find("a", attrs={"data-user-id": True})
        if avatar_a:
            author_img = avatar_a.find("img")
            if author_img:
                author = author_img.get("alt")
            try:
                author_user_id = int(avatar_a["data-user-id"])
            except (ValueError, KeyError):
                pass

        published_at: Optional[str] = None
        time_el = card.find("time")
        if time_el:
            published_at = time_el.get("datetime")

        reading_time: Optional[str] = None
        for li in card.find_all("li", class_="newsCard-date"):
            text = li.get_text(strip=True)
            if "min read" in text:
                # strip SVG title prefix ("Reading time2 min read" → "2 min read")
                m = re.search(r"(\d+\s*min read)", text)
                reading_time = m.group(1) if m else text

        articles.append(NewsArticle(
            thread_id=thread_id,
            title=title,
            url=url,
            thumbnail_url=thumbnail_url,
            author=author,
            author_user_id=author_user_id,
            published_at=published_at,
            reading_time=reading_time,
        ))

    return articles


def parse_news_article(html: str, url: str) -> NewsArticle:
    """Parse a single news article page."""
    soup = BeautifulSoup(html, "html.parser")

    # thread ID from article data attr
    article_el = soup.find("article", class_="newsBody-main")
    thread_id = 0
    if article_el:
        lb_id = article_el.get("data-lb-id", "")
        m = re.search(r"(\d+)", lb_id)
        if m:
            thread_id = int(m.group(1))

    # title
    title_el = soup.find("h1", class_="p-title-value") or soup.find("h1")
    title = title_el.get_text(strip=True) if title_el else ""

    # thumbnail
    thumbnail_url: Optional[str] = None
    thumb_img = soup.find("img", class_="newsView-newsThumbnail-header")
    if thumb_img:
        thumbnail_url = thumb_img.get("src")

    # author + published
    author: Optional[str] = None
    author_user_id: Optional[int] = None
    published_at: Optional[str] = None
    reading_time: Optional[str] = None
    views: Optional[int] = None

    desc = soup.find(class_="p-description")
    if desc:
        author_a = desc.find("a", attrs={"data-user-id": True})
        if author_a:
            author = author_a.get_text(strip=True)
            try:
                author_user_id = int(author_a["data-user-id"])
            except (ValueError, KeyError):
                pass
        time_el = desc.find("time")
        if time_el:
            published_at = time_el.get("datetime")
        for li in desc.find_all("li"):
            text = li.get_text(strip=True)
            if "min read" in text:
                m = re.search(r"(\d+\s*min read)", text)
                reading_time = m.group(1) if m else text

    # view count from pairs--justified
    for pair in soup.find_all(class_="pairs--justified"):
        text = pair.get_text(" ", strip=True)
        m = re.search(r"Views\s+([\d,]+)", text)
        if m:
            try:
                views = int(m.group(1).replace(",", ""))
            except ValueError:
                pass

    # category from breadcrumb
    category: Optional[str] = None
    crumbs = soup.find_all(class_="p-breadcrumbs")
    if not crumbs:
        crumbs = soup.find_all(attrs={"itemprop": "breadcrumb"})
    if crumbs:
        links = crumbs[-1].find_all("a") if crumbs else []
        if links:
            category = links[-1].get_text(strip=True)

    # body
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    bb = soup.find(class_="bbWrapper")
    if bb:
        body_html = str(bb)
        body_text = bb.get_text(" ", strip=True)

    # mentioned IFDB fanedit URLs
    mentioned: List[str] = []
    if bb:
        for a in bb.find_all("a", href=True):
            href = a["href"]
            if "fanedit.org" in href and "/forums/" not in href and href not in mentioned:
                mentioned.append(href)

    return NewsArticle(
        thread_id=thread_id,
        title=title,
        url=url,
        thumbnail_url=thumbnail_url,
        author=author,
        author_user_id=author_user_id,
        published_at=published_at,
        reading_time=reading_time,
        views=views,
        category=category,
        body_html=body_html,
        body_text=body_text,
        mentioned_fanedit_urls=mentioned,
    )
