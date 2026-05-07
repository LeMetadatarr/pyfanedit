# mediavocab Converter

`fanedit_to_release` — `pyfanedit/converters.py:166`

Converts a `FaneditSummary` or `FaneditDetail` to a typed `mediavocab.Release`. Both model types are accepted; `FaneditDetail` populates more fields.

## Usage

```python
from pyfanedit import FaneditClient, fanedit_to_release

client = FaneditClient()
summaries = client.search_by_original_title("Star Wars")

for summary in summaries[:3]:
    detail = client.get_detail(summary.url)
    release = fanedit_to_release(detail)
    work = release.work

    print(work.title, work.variant_kind, work.runtime)
    print(work.external_ids.get("derived_from_imdb"))
```

## Field Mapping

| IFDB field | mediavocab destination | Notes |
|---|---|---|
| `title` | `Work.title` | |
| `title` | `Work.edition`, `Release.edition` | Only when title carries `"Director's Cut"` / `"Edition"` / `"Recut"` / `"Redux"` suffix — `pyfanedit/converters.py:145` |
| `cover_url` | `Release.image` | |
| `url` | `Release.uri` | |
| `faneditor` | `Work.credits[0]` | `RelationRole.EDITOR`, `EntityKind.PERSON` |
| `fanedit_type` | `Work.variant_kind` | `FANEDIT` / `EXTENDED` / `TV_TO_MOVIE` / `MOVIE_TO_TV` / `PRESERVATION` / `OTHER` |
| `fanedit_type` | `Work.extra["fanedit_subtype"]` | For `fanfix`, `fanmix`, `fanedit_short` which have no dedicated `VariantKind` |
| `fanedit_id` | `Work.external_ids["fanedit_id"]` | |
| `slug` | `Work.external_ids["fanedit_slug"]` | |
| `imdb_id` (detail only) | `Work.external_ids["derived_from_imdb"]` | Source film's IMDb id — the fanedit has no IMDb listing of its own |
| `imdb_id` (detail only) | `Work.extra["work_relations"]` | `WorkRelation(kind=FANEDIT_OF, target=<source Work>)` serialised to dict |
| `fanedit_running_time` / `running_time` | `Work.runtime` | Seconds; parses `"1h 45m"` / `"105 min"` / `"105"` — `pyfanedit/converters.py:43` |
| `release_information` | `Work.source_format` | Normalised: `BD-25` / `WEB-DL` / `DVD` / `UHD Blu-ray` / `VHS` / … — `pyfanedit/converters.py:116` |
| `available_in` | `Release.resolution` | `720p` / `1080p` / `2160p` — `pyfanedit/converters.py:65` |
| `available_in` | `Release.hdr` | `HDR` / `HDR10` / `HDR10+` / `Dolby Vision` |
| `available_in` | `Release.audio_channels` | `mono` / `stereo` / `surround` / `5.1` / `7.1` |
| `genre` (detail only) | `Work.content_genres` | |
| `release_date` / `fanedit_release_date` | `Release.release_date` | Parsed by mediavocab's `IsoDate` validator |
| `release_date` / `fanedit_release_date` | `Work.year` | First four characters |
| `franchise`, `intention`, `synopsis`, `editor_rating`, `user_rating` | `Work.extra` | |

`PlaybackModality.VIDEO` is stored in `Work.extra["modality"]`.

## MediaType Determination

`MOVIE_TO_TV` recuts produce `MediaType.EPISODIC_SERIES` per mediavocab's "one Work, one MediaType" axiom. All other types produce `MediaType.MOVIE`. — `pyfanedit/converters.py:188`

`TV_TO_MOVIE` recuts: the fanedit Work is `MediaType.MOVIE`; the source Work inserted into `work_relations` is `MediaType.EPISODIC_SERIES`.

## Source-Work Backlink

`Work` has no first-class `relations` field in mediavocab. The canonical pattern is `Work.extra["work_relations"]` — a list of relation dicts serialised from `WorkRelation`. Round-trip:

```python
from mediavocab import WorkRelation, WorkRelationKind

for rel in work.extra.get("work_relations", []):
    if rel.get("kind") == WorkRelationKind.FANEDIT_OF.value:
        relation = WorkRelation(**rel)
        print(relation.target.title, relation.target.external_ids.get("imdb"))
```

`work_relations` is only populated when `imdb_id` is available on the source `FaneditDetail`. — `pyfanedit/converters.py:263`

## Free-text Parsing Notes

- `available_in` parsing (`_parse_available_in`) is conservative: when no marker is recognised, the field stays at mediavocab's default (`""`). — `pyfanedit/converters.py:65`
- `release_information` parsing (`_parse_source_format`) matches the longest pattern first to avoid `BD-25` matching as `BD` followed by a number. — `pyfanedit/converters.py:116`
- `fanedit_running_time` accepts `"1h 45m"`, `"105 min"`, and bare integers (treated as minutes). — `pyfanedit/converters.py:43`
- `Release.release_date` is passed as-is to mediavocab's `IsoDate` validator. If validation fails, `release_date` is dropped rather than failing the whole conversion. — `pyfanedit/converters.py:339`

## See also

- [IDs and Metadata](ids-and-metadata.md)
- [FaneditClient Reference](reference.md)
