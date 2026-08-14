from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from pyfanedit.client import FaneditClient


def _to_dict(obj) -> dict:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return vars(obj)


def export(
    out: str = "fanedits.jsonl",
    limit: int = 0,
    detail: bool = True,
    delay: float = 0.0,
    quiet: bool = False,
) -> None:
    out_path = Path(out)
    seen_path = Path(out + ".seen")

    seen: set[str] = set()
    if seen_path.exists():
        seen.update(u.strip() for u in seen_path.read_text().splitlines() if u.strip())

    client = FaneditClient()
    count = 0

    with out_path.open("a", encoding="utf-8") as fout, seen_path.open("a", encoding="utf-8") as fseen:
        for item in client.crawl(detail=detail, seen=seen):
            fout.write(json.dumps(_to_dict(item), ensure_ascii=False) + "\n")
            fout.flush()
            url = item.url
            fseen.write(url + "\n")
            fseen.flush()
            count += 1
            if not quiet and count % 25 == 0:
                print(f"[dataset] {count} records written")
            if limit and count >= limit:
                break
            if delay:
                time.sleep(delay)

    if not quiet:
        print(f"[dataset] done — {count} records written to {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bulk export fanedit.org to JSONL")
    parser.add_argument("--out", default="fanedits.jsonl")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--no-detail", action="store_true")
    parser.add_argument("--delay", type=float, default=0.0)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    export(
        out=args.out,
        limit=args.limit,
        detail=not args.no_detail,
        delay=args.delay,
        quiet=args.quiet,
    )


if __name__ == "__main__":
    main()
