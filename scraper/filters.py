"""Apply config filters to listings. Unknown values pass (we don't drop data we can't read)."""
from __future__ import annotations

from .models import Listing


def _pets_ok(listing: Listing, wanted: str) -> bool:
    if wanted == "any" or not listing.pets:
        return True
    pets = listing.pets.lower()
    if "no pet" in pets:
        return False
    if wanted == "cats":
        return "cat" in pets or "pet" in pets
    if wanted == "dogs":
        return "dog" in pets or "pet" in pets
    return True


def passes(listing: Listing, f: dict) -> bool:
    if listing.price is not None:
        if f.get("min_price") is not None and listing.price < f["min_price"]:
            return False
        if f.get("max_price") is not None and listing.price > f["max_price"]:
            return False
    if listing.beds is not None and f.get("min_beds") is not None and listing.beds < f["min_beds"]:
        return False
    if (
        listing.baths is not None
        and f.get("min_baths") is not None
        and listing.baths < f["min_baths"]
    ):
        return False
    text = f"{listing.title} {listing.address}".lower()
    if any(kw.lower() in text for kw in f.get("exclude_keywords", [])):
        return False
    return _pets_ok(listing, f.get("pets", "any"))


def apply_filters(listings: list[Listing], f: dict) -> list[Listing]:
    return [l for l in listings if passes(l, f)]
