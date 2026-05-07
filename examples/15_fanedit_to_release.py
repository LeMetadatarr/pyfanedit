"""Convert scraped fanedits to typed ``mediavocab.Release`` objects.

Demonstrates ``fanedit_to_release()``: the IFDB → mediavocab bridge that
lets fanedit metadata slot into the same vocabulary every other provider
speaks.

Highlights:

* ``client.search_by_original_title(...)`` filters by the *source movie's*
  original title (not the fanedit's own title), so "Alien" doesn't drag in
  "Aliens" recuts.
* ``Work.variant_kind`` carries the recut flavour (``FANEDIT`` / ``EXTENDED``
  / ``TV_TO_MOVIE`` / ``MOVIE_TO_TV`` / ``PRESERVATION`` / ``OTHER``).
* ``Work.external_ids["derived_from_imdb"]`` records the source IMDb id —
  the fanedit Work has no IMDb id of its own.
* ``Work.extra["work_relations"]`` holds a serialised
  ``WorkRelation(kind=FANEDIT_OF, target=<source Work>)`` so consumers can
  walk back to the source film.
"""
from __future__ import annotations

import json

from mediavocab import MediaType, VariantKind, WorkRelationKind

from pyfanedit import FaneditClient, fanedit_to_release


def main() -> None:
    client = FaneditClient()

    summaries = client.search_by_original_title("Star Wars")
    if not summaries:
        print("no fanedits found")
        return

    for summary in summaries[:3]:
        detail = client.get_detail(summary.url)
        release = fanedit_to_release(detail)
        work = release.work

        print(f"--- {work.title} ---")
        print(f"  media_type   : {work.media_type.value}")
        print(f"  variant_kind : {work.variant_kind.value if work.variant_kind else None}")
        print(f"  source IMDb  : {work.external_ids.get('derived_from_imdb')}")
        print(f"  fanedit_id   : {work.external_ids.get('fanedit_id')}")

        # MOVIE_TO_TV recuts cross the Work boundary per mediavocab axiom 12.
        if work.variant_kind is VariantKind.MOVIE_TO_TV:
            assert work.media_type == MediaType.EPISODIC_SERIES

        # Source-Work backlink.
        for rel in work.extra.get("work_relations", []):
            if rel.get("kind") == WorkRelationKind.FANEDIT_OF.value:
                target = rel["target"]
                print(f"  FANEDIT_OF   : {target['title']} "
                      f"(imdb={target['external_ids'].get('imdb')})")

        # Round-trips as JSON for downstream pipelines.
        print(json.dumps(release.model_dump(mode="json"), indent=2)[:200], "...")


if __name__ == "__main__":
    main()
