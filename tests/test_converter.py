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

def test_faneditor_becomes_editor_credit():
    """The faneditor IS the recut's editor; mediavocab has a typed
    ``RelationRole.EDITOR`` for exactly this — using ``CREATOR`` would
    erase the distinction between the source movie's director and the
    fanedit's editor."""
    rel = fanedit_to_release(_summary(faneditor="Jane Editor"))
    assert len(rel.work.credits) == 1
    credit = rel.work.credits[0]
    assert credit.entity.name == "Jane Editor"
    assert credit.relation_role == RelationRole.EDITOR
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

def test_detail_imdb_id_promoted_to_derived_from_imdb():
    """The fanedit Work itself has no IMDb id — its *source* movie does.

    Per mediavocab ExternalIds.derived_from_imdb: "parent IMDb tt-id when
    this record IS a variant".
    """
    detail = FaneditDetail(
        fanedit_id=2,
        title="Example",
        url="https://x",
        imdb_id="tt0123456",
    )
    rel = fanedit_to_release(detail)
    assert rel.work.external_ids["derived_from_imdb"] == "tt0123456"
    # Legacy "imdb_id" key must NOT be set — that would imply the fanedit
    # has its own IMDb listing.
    assert "imdb_id" not in rel.work.external_ids


def test_detail_imdb_id_emits_fanedit_of_work_relation():
    """Spec: a fanedit Work links back to its source Work via FANEDIT_OF."""
    from mediavocab import WorkRelationKind

    detail = FaneditDetail(
        fanedit_id=2,
        title="Star Wars: Despecialized",
        original_title="Star Wars",
        url="https://x",
        imdb_id="tt0076759",
        fanedit_type="preservation",
    )
    rel = fanedit_to_release(detail)
    relations = rel.work.extra.get("work_relations") or []
    assert len(relations) == 1
    relation = relations[0]
    assert relation["kind"] == WorkRelationKind.FANEDIT_OF.value
    assert relation["target"]["external_ids"]["imdb"] == "tt0076759"
    assert relation["target"]["title"] == "Star Wars"


def test_no_imdb_id_no_work_relation():
    """Without a known source IMDb id we don't fabricate a FANEDIT_OF link."""
    detail = FaneditDetail(fanedit_id=3, title="x", url="https://x")
    rel = fanedit_to_release(detail)
    assert "work_relations" not in rel.work.extra


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


# ---------------------------------------------------------------------------
# Lifted technical metadata: runtime, source_format, available_in
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text, expected_seconds", [
    ("1h 45m", 6300.0),
    ("2h", 7200.0),
    ("105m", 6300.0),
    ("105 min", 6300.0),
    ("105", 6300.0),
    ("", None),
    (None, None),
    ("garbage", None),
])
def test_runtime_parser(text, expected_seconds):
    from pyfanedit.converters import _parse_runtime_seconds
    assert _parse_runtime_seconds(text) == expected_seconds


def test_runtime_lifted_from_summary():
    rel = fanedit_to_release(_summary(running_time="1h 30m"))
    assert rel.work.runtime == 5400.0


def test_runtime_lifted_from_detail_fanedit_running_time():
    detail = FaneditDetail(
        fanedit_id=1,
        title="Example",
        url="https://x",
        fanedit_running_time="2h 5m",
    )
    rel = fanedit_to_release(detail)
    assert rel.work.runtime == 7500.0


@pytest.mark.parametrize("text, fmt", [
    ("from BD-25", "BD-25"),
    ("Web-DL source", "WEB-DL"),
    ("DVD master", "DVD"),
    ("UHD Blu-ray remux", "UHD Blu-ray"),
    ("digital download", ""),
    (None, ""),
])
def test_source_format_parser(text, fmt):
    from pyfanedit.converters import _parse_source_format
    assert _parse_source_format(text) == fmt


def test_source_format_lifted_to_work_from_release_information():
    detail = FaneditDetail(
        fanedit_id=1,
        title="Example",
        url="https://x",
        release_information="from BD-25",
    )
    rel = fanedit_to_release(detail)
    assert rel.work.source_format == "BD-25"


@pytest.mark.parametrize("text, resolution, hdr, audio", [
    ("HD / Surround Sound", "720p", "", "surround"),
    ("4K HDR10 5.1", "2160p", "HDR10", "5.1"),
    ("1080p Dolby Vision Stereo", "1080p", "Dolby Vision", "stereo"),
    ("SD", "480p", "", ""),
    ("", "", "", ""),
])
def test_available_in_parser(text, resolution, hdr, audio):
    from pyfanedit.converters import _parse_available_in
    assert _parse_available_in(text) == (resolution, hdr, audio)


def test_available_in_lifted_to_release():
    detail = FaneditDetail(
        fanedit_id=1,
        title="Example",
        url="https://x",
        available_in="HD Surround Sound",
    )
    rel = fanedit_to_release(detail)
    assert rel.resolution == "720p"
    assert rel.audio_channels == "surround"


# ---------------------------------------------------------------------------
# Edition extraction
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("title, edition", [
    ("Star Wars: The Despecialized Edition", "The Despecialized Edition"),
    ("Aliens: Director's Cut", "Director's Cut"),
    ("Blade Runner: Final Cut", "Final Cut"),
    ("Just A Title", ""),
    ("Some Movie: A Recut Story", "A Recut Story"),
])
def test_edition_extraction(title, edition):
    from pyfanedit.converters import _extract_edition
    assert _extract_edition(title) == edition


def test_edition_propagates_to_work_and_release():
    rel = fanedit_to_release(_summary(title="Star Wars: The Despecialized Edition"))
    assert rel.work.edition == "The Despecialized Edition"
    assert rel.edition == "The Despecialized Edition"


# ---------------------------------------------------------------------------
# Content genres
# ---------------------------------------------------------------------------

def test_content_genres_lifted_from_detail():
    detail = FaneditDetail(
        fanedit_id=1,
        title="Example",
        url="https://x",
        genre=["Action", "Sci-Fi"],
    )
    rel = fanedit_to_release(detail)
    # Inherited from source movie; mediavocab content_genres is the typed home.
    assert rel.work.content_genres == ["Action", "Sci-Fi"]
    # Also kept in extra for round-trip with the legacy "genres" key.
    assert rel.work.extra["genres"] == ["Action", "Sci-Fi"]


# ---------------------------------------------------------------------------
# release_date — must round-trip via mediavocab's IsoDate validator (no
# manual datetime parsing in the converter).
# ---------------------------------------------------------------------------

def test_release_date_iso_round_trip():
    detail = FaneditDetail(
        fanedit_id=1,
        title="Example",
        url="https://x",
        fanedit_release_date="2022-07-15",
    )
    rel = fanedit_to_release(detail)
    assert rel.release_date == "2022-07-15"
