"""Unit tests for ``pyfanedit.converters.fanedit_to_release``.

Cover the fanedit-type → (VariantKind, MediaType, fanedit_subtype) mapping,
edition-only label values, and the ``FaneditDetail`` field promotions
(franchise / genres / IMDb id).
"""
from __future__ import annotations

import pytest
from mediavocab import MediaType, RelationRole, VariantKind

from pyfanedit.converters import fanedit_to_release
from pyfanedit.models import FaneditDetail, FaneditSummary


def _summary(**kwargs) -> FaneditSummary:
    base = dict(
        fanedit_id=1,
        slug="example",
        title="Example Fan Edit",
        url="https://fanedit.example/edit",
        cover_url="https://example/cover.jpg",
        faneditor="Some Faneditor",
        fanedit_type="special",
    )
    base.update(kwargs)
    return FaneditSummary(**base)


# ---------------------------------------------------------------------------
# Mapping: fanedit_type → VariantKind / MediaType / fanedit_subtype
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw_type, expected_variant, expected_media, expected_subtype",
    [
        ("fanfix",       VariantKind.FANEDIT,      MediaType.MOVIE,           "fanfix"),
        ("fanmix",       VariantKind.FANEDIT,      MediaType.MOVIE,           "fanmix"),
        ("shorts",       VariantKind.FANEDIT,      MediaType.MOVIE,           "fanedit_short"),
        ("special",      VariantKind.FANEDIT,      MediaType.MOVIE,           None),
        ("extended",     VariantKind.EXTENDED,     MediaType.MOVIE,           None),
        ("preservation", VariantKind.PRESERVATION, MediaType.MOVIE,           None),
        ("documentary",  VariantKind.OTHER,        MediaType.MOVIE,           None),
        ("tv_to_movie",  VariantKind.TV_TO_MOVIE,  MediaType.MOVIE,           None),
        # Per spec axiom 12, MOVIE_TO_TV produces an EPISODIC_SERIES Work.
        ("movie_to_tv",  VariantKind.MOVIE_TO_TV,  MediaType.EPISODIC_SERIES, None),
    ],
)
def test_type_mapping(raw_type, expected_variant, expected_media, expected_subtype):
    rel = fanedit_to_release(_summary(fanedit_type=raw_type))
    assert rel.work.variant_kind == expected_variant
    assert rel.work.media_type == expected_media
    assert rel.work.extra.get("fanedit_subtype") == expected_subtype
    # variant_kind must propagate to the Release as well so consumers can
    # filter editions without inspecting work fields.
    assert rel.variant_kind == expected_variant


def test_unknown_type_falls_back_to_fanedit():
    rel = fanedit_to_release(_summary(fanedit_type="brand_new_kind"))
    assert rel.work.variant_kind == VariantKind.FANEDIT
    assert rel.work.media_type == MediaType.MOVIE
    assert "fanedit_subtype" not in rel.work.extra


def test_missing_type_defaults_to_fanedit():
    rel = fanedit_to_release(_summary(fanedit_type=None))
    assert rel.work.variant_kind == VariantKind.FANEDIT


# ---------------------------------------------------------------------------
# Faneditor credit
# ---------------------------------------------------------------------------

def test_faneditor_becomes_creator_credit():
    rel = fanedit_to_release(_summary(faneditor="Jane Editor"))
    assert len(rel.work.credits) == 1
    credit = rel.work.credits[0]
    assert credit.entity.name == "Jane Editor"
    assert credit.relation_role == RelationRole.CREATOR
    assert credit.role == "editor"


def test_no_faneditor_no_credit():
    rel = fanedit_to_release(_summary(faneditor=None))
    assert rel.work.credits == []


# ---------------------------------------------------------------------------
# external_ids and Release fields
# ---------------------------------------------------------------------------

def test_external_ids_carry_fanedit_metadata():
    rel = fanedit_to_release(_summary(fanedit_id=42, slug="example"))
    assert rel.work.external_ids["fanedit_id"] == "42"
    assert rel.work.external_ids["fanedit_slug"] == "example"


def test_uri_and_image_carried_to_release():
    rel = fanedit_to_release(_summary(
        url="https://fanedit.example/x",
        cover_url="https://fanedit.example/x.jpg",
    ))
    assert rel.uri == "https://fanedit.example/x"
    assert rel.image == "https://fanedit.example/x.jpg"


# ---------------------------------------------------------------------------
# Year extraction
# ---------------------------------------------------------------------------

def test_year_extracted_from_summary_release_date():
    rel = fanedit_to_release(_summary(release_date="2018-05-04"))
    assert rel.work.year == 2018


def test_year_extracted_from_detail_fanedit_release_date():
    detail = FaneditDetail(
        fanedit_id=1,
        title="Example",
        url="https://x",
        faneditor="X",
        fanedit_type="fanfix",
        release_date="2010-01-01",
        fanedit_release_date="2022-07-15",
    )
    rel = fanedit_to_release(detail)
    # FaneditDetail's fanedit_release_date wins (this is the *recut* year,
    # not the original work's year).
    assert rel.work.year == 2022


def test_invalid_release_date_yields_no_year():
    rel = fanedit_to_release(_summary(release_date="???"))
    assert rel.work.year is None


# ---------------------------------------------------------------------------
# FaneditDetail-only fields
# ---------------------------------------------------------------------------

def test_detail_imdb_id_promoted_to_external_ids():
    detail = FaneditDetail(
        fanedit_id=2,
        title="Example",
        url="https://x",
        imdb_id="tt0123456",
    )
    rel = fanedit_to_release(detail)
    assert rel.work.external_ids["imdb_id"] == "tt0123456"


def test_detail_franchise_and_genre_in_extra():
    detail = FaneditDetail(
        fanedit_id=3,
        title="Example",
        url="https://x",
        franchise=["Star Wars"],
        genre=["Action", "Sci-Fi"],
        intention="Restore the original cut.",
    )
    rel = fanedit_to_release(detail)
    assert rel.work.extra["franchise"] == ["Star Wars"]
    assert rel.work.extra["genres"] == ["Action", "Sci-Fi"]
    assert rel.work.extra["intention"] == "Restore the original cut."


def test_summary_synopsis_in_extra():
    rel = fanedit_to_release(_summary(synopsis="A re-edited masterpiece."))
    assert rel.work.extra["synopsis"] == "A re-edited masterpiece."
