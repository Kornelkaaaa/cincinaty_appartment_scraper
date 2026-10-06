"""Apartments.com search results for Oakley (browser-based; the site blocks plain HTTP)."""
from __future__ import annotations

from bs4 import BeautifulSoup

from ..browser import browser_page, goto
from ..models import Listing, parse_beds, parse_price
from .base import Source

BASE = "https://www.apartments.com"


def _text(el) -> str:
    return el.get_text(" ", strip=True) if el else ""


def parse_cards(html: str, source: str) -> list[Listing]:
    soup = BeautifulSoup(html, "lxml")
    out: list[Listing] = []
    for card in soup.select("article.placard, li.mortar-wrapper article"):
        url = card.get("data-url") or ""
        if not url:
            a = card.select_one("a.property-link, a[href]")
            url = a["href"] if a else ""
        if not url:
            continue
        title = _text(card.select_one(".property-title, .js-placardTitle")) or card.get(
            "data-streetaddress", ""
        )
        address = _text(card.select_one(".property-address, .property-address-wrapper"))
        pets = "pets ok" if card.select_one(".petFriendly, .pet-friendly, [title*='Pet']") else ""
        # Newer cards list each bed type with its own price.
        rows = card.select(".priceBedRangeInfo li, .priceGridModelWrapper")
        added = False
        for row in rows:
            beds_txt = _text(row.select_one(".priceBedRangeInfoInnerContainer .bedTextBox, .bedTextBox, .modelName"))
            price_txt = _text(row.select_one(".priceTextBox, .rentLabel"))
            if not (beds_txt or price_txt):
                continue
            out.append(
                Listing(source=source, title=f"{title} – {beds_txt}".strip(" –"), url=url,
                        price=parse_price(price_txt), beds=parse_beds(beds_txt),
                        address=address, pets=pets)
            )
            added = True
        if not added:
            price_txt = _text(card.select_one(".property-pricing, .price-range, .property-rents"))
            beds_txt = _text(card.select_one(".property-beds, .bed-range"))
            out.append(
                Listing(source=source, title=title, url=url, price=parse_price(price_txt),
                        beds=parse_beds(beds_txt), address=address, pets=pets)
            )
    return out


class ApartmentsCom(Source):
    name = "Apartments.com"

    def scrape(self) -> list[Listing]:
        slug = f"{self.area['neighborhood'].lower().replace(' ', '-')}-cincinnati-oh"
        listings: list[Listing] = []
        with browser_page(self.headless) as page:
            for n in range(1, self.max_pages + 1):
                url = f"{BASE}/{slug}/" + ("" if n == 1 else f"{n}/")
                self.log.info("GET %s", url)
                html = goto(page, url, self.delay, wait_for="article.placard",
                            captcha_wait=self.captcha_wait)
                found = parse_cards(html, self.name)
                if not found:
                    break
                listings += found
                if f"/{slug}/{n + 1}/" not in html:  # no next page link
                    break
        return listings
