"""One-off diagnostic: check whether Danish rental portals are reachable
and what their listing pages look like, before we design a scraper.

Run locally (this cloud session's network policy blocks arbitrary outbound
domains, so this must run on a machine with normal internet access):

    python scripts/check_denmark_sources.py

Saves each page's HTML next to this script for inspection.
"""

from __future__ import annotations

import httpx

SOURCES = {
    "boligzonen": "https://boligzonen.dk/ledige-lejeboliger/find",
    "akutbolig": "https://akutbolig.dk/",
    "kvikbolig": "https://www.kvikbolig.dk/",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AIRealtorResearch/1.0)"}


def main() -> None:
    for name, url in SOURCES.items():
        print(f"--- {name}: {url} ---")
        try:
            response = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
            print(f"status={response.status_code} bytes={len(response.text)}")
            out_path = f"scripts/{name}_sample.html"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"saved -> {out_path}")
        except Exception as exc:  # noqa: BLE001 - diagnostic script
            print(f"ERROR: {type(exc).__name__}: {exc}")
        print()


if __name__ == "__main__":
    main()
