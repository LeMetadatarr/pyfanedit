from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ReviewRatings(BaseModel):
    overall: Optional[float] = None
    audio_video_quality: Optional[float] = None
    audio_editing: Optional[float] = None
    visual_editing: Optional[float] = None
    narrative: Optional[float] = None
    enjoyment: Optional[float] = None


class Review(BaseModel):
    reviewer: Optional[str] = None
    reviewer_url: Optional[str] = None
    reviewer_rank: Optional[str] = None
    reviewer_review_count: Optional[int] = None
    date: Optional[str] = None
    ratings: ReviewRatings = Field(default_factory=ReviewRatings)
    body: Optional[str] = None
    discussion_url: Optional[str] = None
    helpful_yes: Optional[int] = None
    helpful_no: Optional[int] = None


class FaneditSummary(BaseModel):
    """Lightweight fanedit as returned from list/search pages."""
    # Canonical IDs
    fanedit_id: Optional[int] = None        # WordPress post ID — stable numeric ID
    slug: Optional[str] = None             # URL slug, e.g. "star-wars-begins"

    title: str
    url: str
    cover_url: Optional[str] = None
    faneditor: Optional[str] = None
    original_title: Optional[str] = None
    fanedit_type: Optional[str] = None
    franchise: Optional[str] = None
    release_date: Optional[str] = None
    running_time: Optional[str] = None
    synopsis: Optional[str] = None
    editor_rating: Optional[float] = None
    user_rating: Optional[float] = None
    user_rating_count: Optional[int] = None
    views: Optional[int] = None
    updated: Optional[str] = None


class FaneditDetail(BaseModel):
    """Full fanedit detail as parsed from its own page."""
    # Canonical IDs
    fanedit_id: Optional[int] = None        # WordPress post ID — stable numeric ID
    slug: Optional[str] = None             # URL slug

    title: str
    url: str
    cover_url: Optional[str] = None
    faneditor: Optional[str] = None
    original_title: Optional[str] = None
    genre: Optional[List[str]] = None
    franchise: Optional[List[str]] = None
    fanedit_type: Optional[str] = None

    # Source film metadata
    original_release_date: Optional[str] = None
    original_running_time: Optional[str] = None
    imdb_id: Optional[str] = None          # e.g. "tt0076759" — from embedded IMDB link

    # Edit metadata
    fanedit_release_date: Optional[str] = None
    fanedit_running_time: Optional[str] = None
    time_cut: Optional[str] = None
    time_added: Optional[str] = None
    subtitles: Optional[str] = None
    available_in: Optional[str] = None     # HD / SD / Surround Sound etc.
    release_information: Optional[str] = None  # Digital / Physical etc.

    # Content
    synopsis: Optional[str] = None
    additional_notes: Optional[str] = None
    special_thanks: Optional[str] = None
    cuts_and_additions: Optional[str] = None
    intention: Optional[str] = None         # editor's stated intent
    awards: Optional[str] = None            # e.g. Fanedit of the Month

    # Ratings
    editor_rating: Optional[float] = None
    user_rating: Optional[float] = None
    user_rating_count: Optional[int] = None

    # Reviews
    editor_reviews: List[Review] = Field(default_factory=list)
    user_reviews: List[Review] = Field(default_factory=list)

    # Raw overflow for any unmapped fields
    extra_fields: Dict[str, str] = Field(default_factory=dict)


class ReviewerEntry(BaseModel):
    """One row from the reviewer leaderboard."""
    rank: int
    user_id: int                    # numeric jReviews user ID (stable)
    username: str
    profile_url: str                # /members/{username}/
    reviews_url: str                # /my-reviews/{user_id}/
    review_count: int
    helpful_yes: Optional[int] = None
    helpful_pct: Optional[float] = None  # e.g. 76.61


class UserReviewEntry(BaseModel):
    """One review from a user's review list page."""
    fanedit_title: str
    fanedit_url: str
    fanedit_type: Optional[str] = None
    date: Optional[str] = None
    ratings: ReviewRatings = Field(default_factory=ReviewRatings)
    discussion_url: Optional[str] = None
    comment_count: Optional[int] = None


class NewsArticle(BaseModel):
    """A news article from the front page or article page."""
    # from listing card
    thread_id: int                  # XenForo thread ID
    title: str
    url: str                        # full URL to article
    thumbnail_url: Optional[str] = None
    author: Optional[str] = None
    author_user_id: Optional[int] = None
    published_at: Optional[str] = None  # ISO datetime string
    reading_time: Optional[str] = None
    # from article page (only when fetched individually)
    views: Optional[int] = None
    category: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    mentioned_fanedit_urls: List[str] = Field(default_factory=list)
