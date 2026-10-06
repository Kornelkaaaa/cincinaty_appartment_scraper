"""Zillow rentals for Oakley. Uses a real browser and reads the embedded Next.js JSON."""
from __future__ import annotations

import json
import re

from ..browser import browser_page, goto
from ..models import Listing, parse_beds, parse_price
from .base import Source

BASE = "https://www.zillow.com"


def _slug(area: dict) -> str:
    return f"{area['neighborhood'].lower().replace(' ', '-')}-cincinnati-oh"


def extract_results(html: str) -> list[dict]:
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return []
    data = json.loads(m.group(1))
    try:
        state = data["props"]["pageProps"]["searchPageState"]
    except (KeyError, TypeError):
        return []
    return (state.get("cat1") or {}).get("searchResults", {}).get("listResults", []) or []


def to_listings(results: list[dict], source: str) -> list[Listing]:
    out: list[Listing] = []
    for r in results:
        url = r.get("detailUrl") or ""
        if url.startswith("/"):
            url = BASE + url
        address = r.get("address") or ""
        title = r.get("buildingName") or r.get("statusText") or address
        units = r.get("units") or []
        if units:  # apartment building: one row per floorplan/unit type
            for u in units:
                beds = u.get("beds")
                out.append(
                    Listing(
                        source=source,
                        title=f"{title} – {'Studio' if str(beds) == '0' else f'{beds} bd'}",
                        url=url,
                        price=parse_price(u.get("price")),
                        beds=parse_beds(f"{beds} bd") if beds not in (None, "") else None,
                        address=address,
                    )
                )
            continue
        price = r.get("unformattedPrice") or parse_price(r.get("price"))
        out.append(
            Listing(
                source=source,
                title=title,
                url=url,
                price=int(price) if price else None,
                beds=float(r["beds"]) if r.get("beds") is not None else None,
                baths=float(r["baths"]) if r.get("baths") is not None else None,
                sqft=int(r["area"]) if r.get("area") else None,
                address=address,
            )
        )
    return out


class Zillow(Source):
    name = "Zillow"

    def scrape(self) -> list[Listing]:
        listings: list[Listing] = []
        with browser_page(self.headless) as page:
            for n in range(1, self.max_pages + 1):
                suffix = "" if n == 1 else f"{n}_p/"
                url = f"{BASE}/{_slug(self.area)}/rentals/{suffix}"
                self.log.info("GET %s", url)
                html = goto(page, url, self.delay, wait_for="#__NEXT_DATA__",
                            captcha_wait=self.captcha_wait)
                results = extract_results(html)
                if not results:
                    break
                listings += to_listings(results, self.name)
                if len(results) < 40:  # last page
                    break
        return listings
