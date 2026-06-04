"""Converters from pyfanedit models to mediavocab typed objects."""
from __future__ import annotations

import re
from typing import Optional, Tuple, Union

from mediavocab import (
    Credit,
    CreditSection as MvCreditSection,
    EntityKind,
    EntityRef,
    MediaType,
    PlaybackType,
    RelationRole,
    Release as MvRelease,
    StreamMode,
    VariantKind,
    Work,
    WorkRelation,
    WorkRelationKind,
)

from pyfanedit.models import FaneditDetail, FaneditSummary


# Map fanedit.org "fanedit_type" raw values to (mediavocab.VariantKind,
# fanedit_subtype). Sub-types intentionally absent from the foundation
# (fanfix, fanmix, fanedit_short) live in the free-text subtype slot in
# `Work.extra` per spec §4.2.
_FANEDIT_TYPE_MAP: dict = {
    "fanfix":        (VariantKind.FANEDIT,     "fanfix"),
    "fanmix":        (VariantKind.FANEDIT,     "fanmix"),
    "extended":      (VariantKind.EXTENDED,    None),
    "tv_to_movie":   (VariantKind.TV_TO_MOVIE, None),
    "movie_to_tv":   (VariantKind.MOVIE_TO_TV, None),
    "shorts":        (VariantKind.FANEDIT,     "fanedit_short"),
    "special":       (VariantKind.FANEDIT,     None),
    "preservation":  (VariantKind.PRESERVATION, None),
    "documentary":   (VariantKind.OTHER,       None),
}


def _parse_runtime_seconds(text: Optional[str]) -> Optional[float]:
    """Parse IFDB runtime strings (``"1h 45m"`` / ``"105 min"`` / ``"105"``) → seconds.

    Returns ``None`` for empty / unrecognised input. mediavocab's ``Work.runtime``
    is documented as seconds.
    """
    if not text:
        return None
    s = text.strip().lower()
    h_m = re.search(r"(\d+)\s*h", s)
    m_m = re.search(r"(\d+)\s*m(?:in)?", s)
    if h_m or m_m:
        hours = int(h_m.group(1)) if h_m else 0
        minutes = int(m_m.group(1)) if m_m else 0
        return float(hours * 3600 + minutes * 60)
    # bare number → assume minutes (IFDB default)
    bare = re.match(r"^\s*(\d+(?:\.\d+)?)\s*$", s)
    if bare:
        return float(bare.group(1)) * 60.0
    return None


def _parse_available_in(text: Optional[str]) -> Tuple[str, str, str]:
    """Lift ``(resolution, hdr, audio_channels)`` hints from IFDB ``available_in``.

    IFDB's "available in" field is free-text combining resolution
    ("HD" / "SD" / "4K") with audio descriptors ("Surround Sound",
    "Stereo", "5.1"). Empty strings mean "no hint" (mediavocab's
    convention for the str fields).
    """
    if not text:
        return "", "", ""
    s = text.lower()
    # Resolution
    if re.search(r"\b(uhd|4k|2160p?)\b", s):
        resolution = "2160p"
    elif re.search(r"\b(qhd|1440p)\b", s):
        resolution = "1440p"
    elif re.search(r"\b(fhd|1080p|full\s*hd)\b", s):
        resolution = "1080p"
    elif re.search(r"\b(hd|720p)\b", s):
        resolution = "720p"
    elif re.search(r"\b(sd|480p|dvd)\b", s):
        resolution = "480p"
    else:
        resolution = ""
    # HDR
    if re.search(r"\b(dolby\s*vision|dv)\b", s):
        hdr = "Dolby Vision"
    elif re.search(r"\bhdr10\+", s):
        hdr = "HDR10+"
    elif re.search(r"\bhdr10\b", s):
        hdr = "HDR10"
    elif re.search(r"\bhdr\b", s):
        hdr = "HDR"
    else:
        hdr = ""
    # Audio channels
    if re.search(r"\b7\.1\b", s):
        audio_channels = "7.1"
    elif re.search(r"\b5\.1\b", s):
        audio_channels = "5.1"
    elif re.search(r"\bsurround\b", s):
        audio_channels = "surround"
    elif re.search(r"\bstereo\b", s):
        audio_channels = "stereo"
    elif re.search(r"\bmono\b", s):
        audio_channels = "mono"
    else:
        audio_channels = ""
    return resolution, hdr, audio_channels


def _parse_source_format(text: Optional[str]) -> str:
    """Lift a normalised source-format token from IFDB ``release_information``.

    IFDB free-text examples: "from BD-25", "Web-DL source", "DVD master".
    Returns ``""`` when no marker is recognised (mediavocab's default).
    """
    if not text:
        return ""
    s = text.lower()
    patterns = [
        (r"\bbd[\s-]*100\b",       "BD-100"),
        (r"\bbd[\s-]*66\b",        "BD-66"),
        (r"\bbd[\s-]*50\b",        "BD-50"),
        (r"\bbd[\s-]*25\b",        "BD-25"),
        (r"\buhd\s*blu[\s-]*ray|\b4k\s*blu[\s-]*ray|\buhd[\s-]*bd\b", "UHD Blu-ray"),
        (r"\bblu[\s-]*ray|\bbd\b", "Blu-ray"),
        (r"\bweb[\s-]*dl\b",       "WEB-DL"),
        (r"\bweb[\s-]*rip\b",      "WEBRip"),
        (r"\bhdtv\b",              "HDTV"),
        (r"\bdvd\b",               "DVD"),
        (r"\bvhs\b",               "VHS"),
        (r"\blaser\s*disc|ld\b",   "LaserDisc"),
    ]
    for pat, label in patterns:
        if re.search(pat, s):
            return label
    return ""


def _extract_edition(title: str) -> str:
    """Pull a free-text edition name out of an IFDB title.

    IFDB titles sometimes carry trailing edition annotations:
    ``"Star Wars: The Despecialized Edition"`` →
    ``"The Despecialized Edition"``. Returns ``""`` when no marker is
    found — never invent an edition.
    """
    if not title:
        return ""
    # Match "<...>: <Foo Edition / Cut / Version>"
    m = re.search(
        r":\s*(.+?\b(?:edition|cut|version|recut|redux)\b.*)$",
        title,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    return ""


def fanedit_to_release(fanedit: Union[FaneditSummary, FaneditDetail]) -> MvRelease:
    """Convert a ``FaneditSummary`` or ``FaneditDetail`` to a mediavocab ``Release``.

    Per spec axiom 12 ("one Work, one MediaType"), a fanedit that crosses the
    MOVIE↔EPISODIC_SERIES boundary (TV_TO_MOVIE / MOVIE_TO_TV) is a *new*
    Work whose ``media_type`` reflects the recut form. The link back to the
    source is the consumer's responsibility (typically a
    ``WorkRelation(kind=FANEDIT_OF, target=source)``).
    """
    # ------------------------------------------------------------------
    # Credit: the faneditor is the EDITOR of the recut.
    # ------------------------------------------------------------------
    credits: list = []
    if fanedit.faneditor:
        ref = EntityRef(name=fanedit.faneditor, kind=EntityKind.PERSON)
        credits.append(Credit(entity=ref, role="editor",
                               relation_role=RelationRole.EDITOR,
                               section=MvCreditSection.PRINCIPAL))

    raw_type = (fanedit.fanedit_type or "").lower()
    variant_kind, subtype = _FANEDIT_TYPE_MAP.get(raw_type, (VariantKind.FANEDIT, None))

    # By default a fanedit is a movie-form recut. MOVIE_TO_TV inverts that.
    media_type = (
        MediaType.EPISODIC_SERIES
        if variant_kind is VariantKind.MOVIE_TO_TV
        else MediaType.MOVIE
    )

    extra: dict = {}
    if fanedit.fanedit_type:
        extra["fanedit_type"] = fanedit.fanedit_type
    if subtype:
        extra["fanedit_subtype"] = subtype
    if fanedit.synopsis:
        extra["synopsis"] = fanedit.synopsis
    if fanedit.editor_rating is not None:
        extra["editor_rating"] = fanedit.editor_rating
    if fanedit.user_rating is not None:
        extra["user_rating"] = fanedit.user_rating

    external_ids: dict = {}
    if fanedit.fanedit_id is not None:
        external_ids["fanedit_id"] = str(fanedit.fanedit_id)
    if fanedit.slug:
        external_ids["fanedit_slug"] = fanedit.slug

    # ------------------------------------------------------------------
    # detail-only fields (rich metadata that only exists on /fanedit/<slug>/)
    # ------------------------------------------------------------------
    source_imdb: Optional[str] = None
    content_genres: list = []
    available_in: Optional[str] = None
    release_info: Optional[str] = None
    runtime_text: Optional[str] = None

    if isinstance(fanedit, FaneditDetail):
        if fanedit.imdb_id:
            # The fanedit Work itself has no IMDb id — its source movie does.
            # Per mediavocab ExternalIds.derived_from_imdb: "parent IMDb tt-id
            # when this record IS a variant".
            external_ids["derived_from_imdb"] = fanedit.imdb_id
            source_imdb = fanedit.imdb_id
        if fanedit.franchise:
            extra["franchise"] = fanedit.franchise
        if fanedit.genre:
            extra["genres"] = fanedit.genre
            content_genres = list(fanedit.genre)
        if fanedit.intention:
            extra["intention"] = fanedit.intention
        available_in = fanedit.available_in
        release_info = fanedit.release_information
        runtime_text = fanedit.fanedit_running_time
    else:
        runtime_text = fanedit.running_time

    # ------------------------------------------------------------------
    # Year — fanedit recut year, NOT the source movie's year.
    # ------------------------------------------------------------------
    year: Optional[int] = None
    if isinstance(fanedit, FaneditDetail) and fanedit.fanedit_release_date:
        try:
            year = int(str(fanedit.fanedit_release_date)[:4])
        except (ValueError, TypeError):
            pass
    elif getattr(fanedit, "release_date", None):
        try:
            year = int(str(fanedit.release_date)[:4])
        except (ValueError, TypeError):
            pass

    # ------------------------------------------------------------------
    # FANEDIT_OF source-Work backlink. ``Work`` has no first-class
    # ``relations`` field in mediavocab — the canonical home for a typed
    # ``WorkRelation`` is ``Work.extra["work_relations"]`` (a JSON-serialised
    # list of relation dicts). Consumers deserialise via
    # ``WorkRelation(**rel_dict)`` to round-trip.
    # ------------------------------------------------------------------
    if source_imdb:
        source_media = (
            MediaType.EPISODIC_SERIES
            if variant_kind is VariantKind.TV_TO_MOVIE
            else MediaType.MOVIE
        )
        source_work = Work(
            title=fanedit.original_title or fanedit.title,
            media_type=source_media,
            external_ids={"imdb": source_imdb},
        )
        relation = WorkRelation(kind=WorkRelationKind.FANEDIT_OF, target=source_work)
        extra["work_relations"] = [relation.model_dump(mode="json")]

    # ------------------------------------------------------------------
    # Release-level publication date (recut date, parsed by mediavocab's
    # IsoDate validator — no manual datetime parsing here).
    # ------------------------------------------------------------------
    release_date_str: Optional[str] = None
    if isinstance(fanedit, FaneditDetail) and fanedit.fanedit_release_date:
        release_date_str = fanedit.fanedit_release_date
    elif getattr(fanedit, "release_date", None):
        release_date_str = fanedit.release_date

    # PlaybackType.VIDEO — fanedits are always video works.
    extra.setdefault("modality", PlaybackType.VIDEO.value)

    # ------------------------------------------------------------------
    # Lifted technical metadata from IFDB free-text fields.
    # ------------------------------------------------------------------
    runtime_seconds = _parse_runtime_seconds(runtime_text)
    edition_str = _extract_edition(fanedit.title)
    source_format = _parse_source_format(release_info)
    resolution, hdr, audio_channels = _parse_available_in(available_in)

    work_kwargs: dict = dict(
        title=fanedit.title,
        media_type=media_type,
        year=year,
        variant_kind=variant_kind,
        credits=credits,
        external_ids=external_ids,
        extra=extra,
    )
    if runtime_seconds is not None:
        work_kwargs["runtime"] = runtime_seconds
    if edition_str:
        work_kwargs["edition"] = edition_str
    if source_format:
        work_kwargs["source_format"] = source_format
    if content_genres:
        work_kwargs["content_genres"] = content_genres

    work = Work(**work_kwargs)

    # variant_kind lives on the Work only (one source of truth); Release has no
    # such field. Consumers filter editions via ``release.work.variant_kind``.
    release_kwargs: dict = dict(
        work=work,
        uri=fanedit.url,
        image=fanedit.cover_url or "",
        stream_mode=StreamMode.ON_DEMAND,
        external_ids=external_ids,
        extra=extra,
    )
    if edition_str:
        release_kwargs["edition"] = edition_str
    if resolution:
        release_kwargs["resolution"] = resolution
    if hdr:
        release_kwargs["hdr"] = hdr
    if audio_channels:
        release_kwargs["audio_channels"] = audio_channels
    if release_date_str:
        release_kwargs["release_date"] = release_date_str

    try:
        return MvRelease(**release_kwargs)
    except Exception:
        # If the date string fails mediavocab's IsoDate validator, drop it
        # rather than fail the whole conversion.
        release_kwargs.pop("release_date", None)
        return MvRelease(**release_kwargs)
