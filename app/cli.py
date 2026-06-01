from __future__ import annotations

import argparse
import json
import sys

from app.crawler import crawl


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Crawl a URL and return metadata/topics as JSON.")
    parser.add_argument("url", help="Absolute http(s) URL to crawl")
    parser.add_argument("--timeout", type=float, default=10.0, help="Request timeout in seconds")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args(argv)
    try:
        result = crawl(args.url, timeout_seconds=args.timeout)
    except Exception as exc:
        print(json.dumps({"url": args.url, "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result.to_dict(), indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
