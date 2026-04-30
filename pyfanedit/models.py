from typing import Dict, Optional

from pydantic import BaseModel, Field


class FaneditSummary(BaseModel):
    """Lightweight fanedit as returned from list/search pages."""
    listing_id: Optional[str] = None
    title: str
    url: str
    cover_url: Optional[str] = None
    faneditor: Optional[str] = None
    original_title: Optional[str] = None
    fanedit_type: Optional[str] = None
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
    title: str
    url: str
    cover_url: Optional[str] = None
    listing_id: Optional[str] = None
    faneditor: Optional[str] = None
    original_title: Optional[str] = None
    genre: Optional[str] = None
    fanedit_type: Optional[str] = None
    original_release_date: Optional[str] = None
    original_running_time: Optional[str] = None
    fanedit_release_date: Optional[str] = None
    fanedit_running_time: Optional[str] = None
    subtitles: Optional[str] = None
    available_in: Optional[str] = None
    synopsis: Optional[str] = None
    additional_notes: Optional[str] = None
    release_information: Optional[str] = None
    cuts_and_additions: Optional[str] = None
    editor_rating: Optional[float] = None
    user_rating: Optional[float] = None
    user_rating_count: Optional[int] = None
    extra_fields: Dict[str, str] = Field(default_factory=dict)
