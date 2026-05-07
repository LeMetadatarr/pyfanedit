"""07 — Convert fanedits to mediavocab Release objects.

Shows: search_by_original_title(), fanedit_to_release(), variant fan-out,
FANEDIT_OF backlink, Release.resolution / hdr / audio_channels.
"""
from __future__ import annotations

from mediavocab import MediaType, RelationRole, VariantKind, WorkRelationKind

from pyfanedit import FaneditClient, fanedit_to_release

client = FaneditClient()

summaries = client.search_by_original_title("Star Wars")
if not summaries:
    print("no results")
    raise SystemExit

print(f"Found {len(summaries)} fanedits of 'Star Wars'\n")

for summary in summaries[:5]:
    detail = client.get_detail(summary.url)
    release = fanedit_to_release(detail)
    work = release.work

    print(f"  {work.title}")
    print(f"    variant_kind   : {work.variant_kind}")
    print(f"    media_type     : {work.media_type}")
    print(f"    runtime (sec)  : {work.runtime}")
    print(f"    edition        : {work.edition or '(none)'}")
    print(f"    source_format  : {work.source_format or '(unknown)'}")
    print(f"    resolution     : {release.resolution or '(unknown)'}")
    print(f"    hdr            : {release.hdr or '(none)'}")
    print(f"    audio_channels : {release.audio_channels or '(unknown)'}")
    print(f"    derived_from   : {work.external_ids.get('derived_from_imdb')}")

    # EDITOR credit
    for credit in work.credits:
        if credit.relation_role is RelationRole.EDITOR:
            print(f"    EDITOR         : {credit.entity.name}")

    # FANEDIT_OF source-work backlink (in work.extra["work_relations"])
    for rel in work.extra.get("work_relations", []):
        if rel.get("kind") == WorkRelationKind.FANEDIT_OF.value:
            target = rel["target"]
            print(f"    FANEDIT_OF     : {target['title']} "
                  f"(imdb={target['external_ids'].get('imdb')})")

    # MOVIE_TO_TV recuts are reclassified as EPISODIC_SERIES
    if work.variant_kind is VariantKind.MOVIE_TO_TV:
        assert work.media_type == MediaType.EPISODIC_SERIES

    print()
