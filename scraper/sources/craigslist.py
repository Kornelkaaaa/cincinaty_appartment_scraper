"""Craigslist Cincinnati apartments, restricted to a radius around the Oakley ZIP."""
from __future__ import annotations

from urllib.parse import urlencode

from bs4 import BeautifulSoup

from ..http import PoliteSession
from ..models import Listing, parse_baths, parse_beds, parse_price, parse_sqft
from .base import Source

BASE = "https://cincinnati.craigslist.org"


class Craigslist(Source):
    name = "Craigslist"

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        self.http = PoliteSession(self.delay)
        # Fetching each posting gives beds/baths/sqft/pets but costs one request per listing.
        self.fetch_details = bool(cfg["scraping"].get("craigslist_details", True))
        self.max_details = int(cfg["scraping"].get("craigslist_max_details", 60))

    def search_url(self) -> str:
        f = self.cfg["filters"]
        params = {
            "postal": self.area["zip"],
            "search_distance": self.area.get("radius_miles", 1),
            "availabilityMode": 0,
        }
        if f.get("min_price") is not None:
            params["min_price"] = f["min_price"]
        if f.get("max_price") is not None:
            params["max_price"] = f["max_price"]
        if f.get("min_beds"):
            params["min_bedrooms"] = int(f["min_beds"])
        if f.get("pets") == "cats":
            params["pets_cat"] = 1
        elif f.get("pets") == "dogs":
            params["pets_dog"] = 1
        return f"{BASE}/search/apa?{urlencode(params)}"

    def scrape(self) -> list[Listing]:
        url = self.search_url()
        self.log.info("GET %s", url)
        soup = BeautifulSoup(self.http.get(url).text, "lxml")
        listings: list[Listing] = []
        for li in soup.select("li.cl-static-search-result"):
            a = li.find("a", href=True)
            if not a:
                continue
            title_el = li.select_one(".title")
            title = title_el.get_text(strip=True) if title_el else li.get("title", "")
            price_el = li.select_one(".price")
            loc_el = li.select_one(".location")
            listings.append(
                Listing(
                    source=self.name,
                    title=title,
                    url=a["href"],
                    price=parse_price(price_el.get_text() if price_el else None),
                    beds=parse_beds(title),
                    address=loc_el.get_text(strip=True) if loc_el else "",
                )
            )
        self.log.info("%d search results", len(listings))
        if self.fetch_details:
            for listing in listings[: self.max_details]:
                try:
                    self._enrich(listing)
                except Exception as e:  # one bad posting shouldn't kill the run
                    self.log.warning("detail fetch failed for %s: %s", listing.url, e)
        return listings

    def _enrich(self, listing: Listing) -> None:
        soup = BeautifulSoup(self.http.get(listing.url).text, "lxml")
        attrs = [s.get_text(" ", strip=True) for s in soup.select(".attrgroup span, .attrgroup div")]
        pets = []
        for text in attrs:
            low = text.lower()
            if ("br" in low or "ba" in low) and "/" in low:
                listing.beds = parse_beds(low.split("/")[0].replace("br", " br")) or listing.beds
                listing.baths = parse_baths(low.split("/")[1].replace("ba", " ba"))
            elif "ft2" in low:
                listing.sqft = parse_sqft(low)
            elif "cats are ok" in low:
                pets.append("cats")
            elif "dogs are ok" in low:
                pets.append("dogs")
        housing = soup.select_one(".housing")
        if housing and listing.beds is None:
            listing.beds = parse_beds(housing.get_text(" "))
        if pets:
            listing.pets = ", ".join(dict.fromkeys(pets))
        street = soup.select_one(".mapaddress")
        if street:
            listing.address = street.get_text(strip=True)
        posted = soup.select_one("time.date.timeago, time")
        if posted and posted.get("datetime"):
            listing.posted_date = posted["datetime"][:10]
