"""Common listing record and text-parsing helpers shared by all sources."""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from datetime import datetime

_NUM = r"(\d+(?:\.\d+)?)"


@dataclass
class Listing:
    source: str
    title: str
    url: str
    price: int | None = None
    beds: float | None = None
    baths: float | None = None
    sqft: int | None = None
    address: str = ""
    pets: str = ""  # free text, e.g. "cats, dogs" / "no pets" / ""
    posted_date: str = ""
    first_seen: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    is_new: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def parse_price(text: str | None) -> int | None:
    """'$1,450/mo' -> 1450; '$1,200 - $1,600' -> 1200 (lowest)."""
    if not text:
        return None
    m = re.search(r"\$?\s*(\d{1,3}(?:,\d{3})+|\d{3,6})", str(text))
    if not m:
        return None
    value = int(m.group(1).replace(",", ""))
    return value if 200 <= value <= 50000 else None


def parse_beds(text: str | None) -> float | None:
    """'Studio' -> 0; '2 bd' / '2br' / '2 Beds' -> 2; '1-2 Beds' -> 1."""
    if text is None:
        return None
    t = str(text).lower()
    if "studio" in t:
        return 0.0
    m = re.search(_NUM + r"\s*(?:-|–|to)?\s*(?:\d+\s*)?(?:bd|br|bed|bedroom)", t)
    if m:
        return float(m.group(1))
    m = re.fullmatch(r"\s*" + _NUM + r"\s*", t)
    return float(m.group(1)) if m else None


def parse_baths(text: str | None) -> float | None:
    if text is None:
        return None
    t = str(text).lower()
    m = re.search(_NUM + r"\s*(?:-|–|to)?\s*(?:\d+(?:\.\d+)?\s*)?(?:ba|bath)", t)
    if m:
        return float(m.group(1))
    m = re.fullmatch(r"\s*" + _NUM + r"\s*", t)
    return float(m.group(1)) if m else None


def parse_sqft(text: str | None) -> int | None:
    if text is None:
        return None
    t = str(text).lower().replace(",", "")
    m = re.search(r"(\d{3,5})\s*(?:-\s*\d+\s*)?(?:ft2|ft²|sq\.?\s*ft|sqft|square feet)", t)
    if m:
        return int(m.group(1))
    m = re.fullmatch(r"\s*(\d{3,5})\s*", t)
    return int(m.group(1)) if m else None
