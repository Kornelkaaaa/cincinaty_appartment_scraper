"""Generic scraper for individual complex / property-manager sites, driven by CSS selectors in config."""
from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..browser import browser_page, goto
from ..http import PoliteSession
from ..models import Listing, parse_baths, parse_beds, parse_price, parse_sqft
from .base import Source


def _text(card, selector: str | None) -> str:
    if not selector:
        return ""
    el = card.select_one(selector)
    return el.get_text(" ", strip=True) if el else ""


def parse_site(html: str, site: dict) -> list[Listing]:
    sel = site.get("selectors") or {}
    soup = BeautifulSoup(html, "lxml")
    out: list[Listing] = []
    for card in soup.select(sel.get("card", "body")):
        link_el = card.select_one(sel["link"]) if sel.get("link") else None
        if link_el is None and card.name == "a":
            link_el = card
        href = link_el.get("href") if link_el else None
        title = _text(card, sel.get("title")) or site["name"]
        out.append(
            Listing(
                source=site["name"],
                title=title if site["name"] in title else f"{site['name']} – {title}",
                url=urljoin(site["url"], href) if href else site["url"],
                price=parse_price(_text(card, sel.get("price"))),
                beds=parse_beds(_text(card, sel.get("beds"))),
                baths=parse_baths(_text(card, sel.get("baths"))),
                sqft=parse_sqft(_text(card, sel.get("sqft"))),
                address=site.get("address", ""),
                pets=site.get("pets", ""),
            )
        )
    return out


class PropertyManagers(Source):
    name = "Property managers"

    def sites(self) -> list[dict]:
        return [s for s in self.cfg["sources"]["property_managers"] if s.get("enabled", True)]

    def scrape_site(self, site: dict) -> list[Listing]:
        if site.get("browser"):
            with browser_page(self.headless) as page:
                html = goto(page, site["url"], self.delay,
                            wait_for=(site.get("selectors") or {}).get("card"),
                            captcha_wait=self.captcha_wait)
        else:
            html = PoliteSession(self.delay).get(site["url"]).text
        return parse_site(html, site)
