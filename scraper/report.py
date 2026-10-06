"""Render results as a Markdown file."""
from __future__ import annotations

from datetime import datetime

from .models import Listing


def _cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _fmt_num(v) -> str:
    if v is None:
        return "–"
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v)


def _beds(v) -> str:
    return "Studio" if v == 0 else _fmt_num(v)


def _table(listings: list[Listing]) -> list[str]:
    rows = [
        "| Price | Beds | Baths | Sqft | Title / Address | Pets | Source | First seen | Link |",
        "|---:|---:|---:|---:|---|---|---|---|---|",
    ]
    for l in listings:
        price = f"${l.price:,}" if l.price else "–"
        place = _cell(l.title)
        if l.address and l.address.lower() not in l.title.lower():
            place += f"<br>{_cell(l.address)}"
        rows.append(
            f"| {price} | {_beds(l.beds)} | {_fmt_num(l.baths)} | {_fmt_num(l.sqft)} | "
            f"{place} | {_cell(l.pets) or '–'} | {_cell(l.source)} | {l.first_seen} | "
            f"[open]({l.url}) |"
        )
    return rows


def render(listings: list[Listing], cfg: dict, source_status: dict[str, str]) -> str:
    f = cfg["filters"]
    area = cfg["area"]
    listings = sorted(listings, key=lambda l: (l.price is None, l.price or 0))
    new = [l for l in listings if l.is_new]

    def rng(lo, hi, unit=""):
        if lo is None and hi is None:
            return "any"
        return f"{unit}{lo if lo is not None else '0'} – {unit}{hi if hi is not None else '∞'}"

    out = [
        f"# {area['neighborhood']} (Cincinnati, OH {area['zip']}) Apartments",
        "",
        f"_Generated {datetime.now():%Y-%m-%d %H:%M}_",
        "",
        "**Filters:** "
        f"price {rng(f.get('min_price'), f.get('max_price'), '$')} · "
        f"beds ≥ {f.get('min_beds') if f.get('min_beds') is not None else 'any'} · "
        f"baths ≥ {f.get('min_baths') if f.get('min_baths') is not None else 'any'} · "
        f"pets: {f.get('pets', 'any')}",
        "",
        "## Sources",
        "",
        "| Source | Status |",
        "|---|---|",
    ]
    out += [f"| {name} | {_cell(status)} |" for name, status in source_status.items()]
    out += ["", f"**{len(listings)} listings** matched ({len(new)} new since last run).", ""]

    out += ["## 🆕 New since last run", ""]
    out += _table(new) if new else ["_None._"]
    out += ["", "## All listings (sorted by price)", ""]
    out += _table(listings) if listings else ["_No listings matched._"]
    out.append("")
    return "\n".join(out)
