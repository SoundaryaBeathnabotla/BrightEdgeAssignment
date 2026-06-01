from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.crawler import crawl


def iter_urls(path: Path) -> list[str]:
    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if value and not value.startswith("#"):
            urls.append(value)
    return urls


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Crawl a text file of URLs and emit JSONL.")
    parser.add_argument("input_file", type=Path)
    parser.add_argument("--output", type=Path, default=Path("crawl_results.jsonl"))
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args(argv)

    urls = iter_urls(args.input_file)
    with args.output.open("w", encoding="utf-8") as handle:
        for url in urls:
            try:
                payload = crawl(url, timeout_seconds=args.timeout).to_dict()
            except Exception as exc:
                payload = {"url": url, "error": str(exc)}
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
    print(f"Wrote {len(urls)} records to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
