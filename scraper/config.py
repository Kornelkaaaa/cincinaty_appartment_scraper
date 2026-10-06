"""Load config.yaml with sensible defaults."""
from __future__ import annotations

from pathlib import Path

import yaml

DEFAULTS = {
    "area": {"zip": "45209", "neighborhood": "Oakley", "radius_miles": 1},
    "filters": {
        "min_price": None,
        "max_price": None,
        "min_beds": None,
        "min_baths": None,
        "pets": "any",
        "exclude_keywords": [],
    },
    "scraping": {"max_pages": 3, "delay_seconds": [2, 5], "headless": True},
    "sources": {
        "craigslist": True,
        "zillow": True,
        "apartments_com": True,
        "property_managers": [],
    },
}


def _merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(path: str | Path = "config.yaml") -> dict:
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    cfg = _merge(DEFAULTS, data or {})
    pets = str(cfg["filters"].get("pets") or "any").lower()
    if pets not in {"any", "cats", "dogs"}:
        raise ValueError(f"filters.pets must be any|cats|dogs, got {pets!r}")
    cfg["filters"]["pets"] = pets
    cfg["filters"]["exclude_keywords"] = cfg["filters"].get("exclude_keywords") or []
    cfg["sources"]["property_managers"] = cfg["sources"].get("property_managers") or []
    return cfg
