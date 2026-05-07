"""Converters from pyfanedit models to mediavocab typed objects."""
from __future__ import annotations

from typing import Union

from mediavocab import (
    Credit,
    CreditSection as MvCreditSection,
    EntityKind,
    EntityRef,
    MediaType,
    PlaybackModality,
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
    source_imdb: str | None = None
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

    # Link the fanedit Work back to its source Work via FANEDIT_OF.
    # The source is identified by IMDb id only — we don't fetch its full
    # metadata here, so the target Work is a stub carrying just the id.
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
        # Work has no first-class `relations` field; persist via `extra` so
        # consumers (and round-trip serialisers) can recover the lineage.
        extra["work_relations"] = [relation.model_dump(mode="json")]

    # Release-level release_date (recut date for FaneditDetail; original
    # release_date for FaneditSummary). mediavocab parses ISO 8601 strings.
    release_date_str: str | None = None
    if isinstance(fanedit, FaneditDetail) and fanedit.fanedit_release_date:
        release_date_str = fanedit.fanedit_release_date
    elif getattr(fanedit, "release_date", None):
        release_date_str = fanedit.release_date

    # PlaybackModality.VIDEO — fanedits are always video works.
    extra.setdefault("modality", PlaybackModality.VIDEO.value)

    work = Work(
        title=fanedit.title,
        media_type=media_type,
        year=year,
        variant_kind=variant_kind,
        credits=credits,
        external_ids=external_ids,
        extra=extra,
    )
    release_kwargs: dict = dict(
        work=work,
        uri=fanedit.url,
        image=fanedit.cover_url or "",
        variant_kind=variant_kind,
        stream_mode=StreamMode.ON_DEMAND,
        external_ids=external_ids,
        extra=extra,
    )
    if release_date_str:
        release_kwargs["release_date"] = release_date_str
    try:
        return MvRelease(**release_kwargs)
    except Exception:
        # If the date string fails mediavocab's IsoDate validator, drop it
        # rather than fail the whole conversion.
        release_kwargs.pop("release_date", None)
        return MvRelease(**release_kwargs)
