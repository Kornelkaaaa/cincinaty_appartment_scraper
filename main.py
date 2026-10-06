"""Oakley (Cincinnati) apartment scraper.

Usage:
    python main.py                          # all enabled sources
    python main.py --sources craigslist     # just one (craigslist, zillow, apartments_com, property_managers)
    python main.py --out oakley.md --show-browser
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from scraper.config import load_config
from scraper.dedupe import dedupe
from scraper.filters import apply_filters
from scraper.models import Listing
from scraper.report import render
from scraper.sources.apartments_com import ApartmentsCom
from scraper.sources.craigslist import Craigslist
from scraper.sources.property_managers import PropertyManagers
from scraper.sources.zillow import Zillow
from scraper.state import mark_new

SOURCES = {
    "craigslist": Craigslist,
    "zillow": Zillow,
    "apartments_com": ApartmentsCom,
    "property_managers": PropertyManagers,
}


def run_source(key: str, cfg: dict, status: dict[str, str]) -> list[Listing]:
    log = logging.getLogger("scraper")
    source = SOURCES[key](cfg)
    if isinstance(source, PropertyManagers):
        results: list[Listing] = []
        sites = source.sites()
        if not sites:
            status[source.name] = "skipped – no sites enabled in config.yaml"
        for site in sites:
            try:
                found = source.scrape_site(site)
                status[site["name"]] = f"✅ {len(found)} found"
                results += found
            except Exception as e:
                log.warning("%s failed: %s", site["name"], e)
                status[site["name"]] = f"❌ {type(e).__name__}: {e}"
        return results
    try:
        found = source.scrape()
        status[source.name] = f"✅ {len(found)} found"
        return found
    except Exception as e:
        log.warning("%s failed: %s", source.name, e)
        status[source.name] = f"❌ {type(e).__name__}: {str(e)[:150]}"
        return []


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Scrape Oakley, Cincinnati apartment listings to Markdown.")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--out", default="listings.md")
    ap.add_argument("--state", default="seen.json")
    ap.add_argument("--sources", help="comma-separated: " + ",".join(SOURCES))
    ap.add_argument("--show-browser", action="store_true", help="run Playwright non-headless")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    cfg = load_config(args.config)
    if args.show_browser:
        cfg["scraping"]["headless"] = False

    if args.sources:
        keys = [k.strip() for k in args.sources.split(",") if k.strip()]
        unknown = set(keys) - set(SOURCES)
        if unknown:
            ap.error(f"unknown sources: {', '.join(unknown)}")
    else:
        keys = [k for k in SOURCES if cfg["sources"].get(k)]

    status: dict[str, str] = {}
    all_listings: list[Listing] = []
    for key in keys:
        all_listings += run_source(key, cfg, status)

    listings = apply_filters(dedupe(all_listings), cfg["filters"])
    mark_new(listings, args.state)
    Path(args.out).write_text(render(listings, cfg, status), encoding="utf-8")
    logging.getLogger("scraper").info(
        "Wrote %d listings (%d new) to %s", len(listings), sum(l.is_new for l in listings), args.out
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
