"""Remove duplicates across sources (same unit posted on several sites)."""
from __future__ import annotations

import re

from .models import Listing

_ABBREV = {
    "street": "st", "avenue": "ave", "road": "rd", "drive": "dr", "lane": "ln",
    "boulevard": "blvd", "place": "pl", "court": "ct", "apartment": "apt", "unit": "apt",
}


def normalize_address(addr: str) -> str:
    a = addr.lower()
    a = re.sub(r"[#.,]", " ", a)
    words = [_ABBREV.get(w, w) for w in a.split()]
    a = " ".join(words)
    a = re.sub(r"\b(cincinnati|oh|ohio|45209)\b", "", a)
    return re.sub(r"\s+", " ", a).strip()


def listing_key(listing: Listing) -> str:
    addr = normalize_address(listing.address)
    # Only trust addresses that start with a street number.
    if re.match(r"^\d+\s+\w+", addr):
        return f"addr:{addr}|{listing.beds}|{listing.price}"
    return f"url:{listing.url.split('?')[0].rstrip('/')}"


def _score(l: Listing) -> int:
    return sum(v not in (None, "") for v in (l.price, l.beds, l.baths, l.sqft, l.address, l.pets))


def dedupe(listings: list[Listing]) -> list[Listing]:
    best: dict[str, Listing] = {}
    for l in listings:
        k = listing_key(l)
        if k not in best or _score(l) > _score(best[k]):
            if k in best and best[k].source != l.source:
                l.source = f"{l.source}, {best[k].source}"
            best[k] = l
        elif best[k].source != l.source and l.source not in best[k].source:
            best[k].source = f"{best[k].source}, {l.source}"
    return list(best.values())
