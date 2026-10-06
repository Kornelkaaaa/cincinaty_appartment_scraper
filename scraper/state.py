"""Remember listings between runs so new ones can be flagged."""
from __future__ import annotations

import json
from pathlib import Path

from .dedupe import listing_key
from .models import Listing


def mark_new(listings: list[Listing], path: str | Path = "seen.json") -> None:
    path = Path(path)
    seen: dict[str, str] = {}
    if path.exists():
        try:
            seen = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            seen = {}
    first_run = not seen
    for l in listings:
        k = listing_key(l)
        if k in seen:
            l.first_seen = seen[k]
            l.is_new = False
        else:
            seen[k] = l.first_seen
            l.is_new = not first_run
    path.write_text(json.dumps(seen, indent=1, sort_keys=True), encoding="utf-8")
