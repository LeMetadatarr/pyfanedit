"""Converters from pyfanedit models to mediavocab typed objects."""
from __future__ import annotations

from typing import Union

from mediavocab import (
    Credit,
    CreditSection as MvCreditSection,
    EntityKind,
    EntityRef,
    MediaType,
    RelationRole,
    Release as MvRelease,
    StreamMode,
    VariantKind,
    Work,
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


def fanedit_to_release(fanedit: Union[FaneditSummary, FaneditDetail]) -> MvRelease:
    """Convert a ``FaneditSummary`` or ``FaneditDetail`` to a mediavocab ``Release``.

    Per spec axiom 12 ("one Work, one MediaType"), a fanedit that crosses the
    MOVIE↔EPISODIC_SERIES boundary (TV_TO_MOVIE / MOVIE_TO_TV) is a *new*
    Work whose ``media_type`` reflects the recut form. The link back to the
    source is the consumer's responsibility (typically a
    ``WorkRelation(kind=FANEDIT_OF, target=source)``).
    """
    credits: list = []
    if fanedit.faneditor:
        ref = EntityRef(name=fanedit.faneditor, kind=EntityKind.PERSON)
        credits.append(Credit(entity=ref, role="editor",
                               relation_role=RelationRole.CREATOR,
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

    # detail-only fields
    if isinstance(fanedit, FaneditDetail):
        if fanedit.imdb_id:
            external_ids["imdb_id"] = fanedit.imdb_id
        if fanedit.franchise:
            extra["franchise"] = fanedit.franchise
        if fanedit.genre:
            extra["genres"] = fanedit.genre
        if fanedit.intention:
            extra["intention"] = fanedit.intention

    year: int | None = None
    if fanedit.release_date if hasattr(fanedit, "release_date") else None:
        try:
            year = int(str(fanedit.release_date)[:4])
        except (ValueError, TypeError):
            pass
    # FaneditDetail has fanedit_release_date
    if isinstance(fanedit, FaneditDetail) and fanedit.fanedit_release_date:
        try:
            year = int(str(fanedit.fanedit_release_date)[:4])
        except (ValueError, TypeError):
            pass

    work = Work(
        title=fanedit.title,
        media_type=media_type,
        year=year,
        variant_kind=variant_kind,
        credits=credits,
        external_ids=external_ids,
        extra=extra,
    )
    return MvRelease(
        work=work,
        uri=fanedit.url,
        image=fanedit.cover_url or "",
        variant_kind=variant_kind,
        stream_mode=StreamMode.ON_DEMAND,
        external_ids=external_ids,
        extra=extra,
    )
