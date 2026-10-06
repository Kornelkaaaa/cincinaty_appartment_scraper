"""Render results as a single self-contained HTML page with client-side filters."""
from __future__ import annotations

import json
from datetime import datetime
from html import escape

from .models import Listing


def render_html(listings: list[Listing], cfg: dict, source_status: dict[str, str]) -> str:
    area = cfg["area"]
    data = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "defaults": cfg["filters"],
        "status": source_status,
        "listings": [l.to_dict() for l in listings],
    }
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    title = f"{area['neighborhood']} Apartments"
    return (
        TEMPLATE.replace("__TITLE__", escape(title))
        .replace("__SUBTITLE__", escape(f"Cincinnati, OH {area['zip']}"))
        .replace("__DATA__", payload)
    )


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>__TITLE__</title>
<style>
:root{
  --bg:#f6f4ef;--panel:#fffdf8;--ink:#1f2421;--muted:#6b706c;--line:#e3dfd5;
  --accent:#2f6b4f;--accent-ink:#fff;--new:#c2410c;--chip:#ece8de;--star:#d99a06;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#141715;--panel:#1c201e;--ink:#e8ebe7;--muted:#9aa19c;--line:#2c322f;
  --accent:#6fbf94;--accent-ink:#0d1410;--new:#fb923c;--chip:#262b28;--star:#f5c542;}}
:root[data-theme="dark"]{
  --bg:#141715;--panel:#1c201e;--ink:#e8ebe7;--muted:#9aa19c;--line:#2c322f;
  --accent:#6fbf94;--accent-ink:#0d1410;--new:#fb923c;--chip:#262b28;--star:#f5c542;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
header{padding:28px 16px 12px;max-width:1200px;margin:0 auto}
h1{margin:0;font-size:28px;letter-spacing:-.02em}
.sub{color:var(--muted);margin-top:2px}
.wrap{max-width:1200px;margin:0 auto;padding:0 16px 48px;display:grid;grid-template-columns:260px 1fr;gap:24px}
aside{position:sticky;top:12px;align-self:start;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px}
aside h3{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:16px 0 8px}
aside h3:first-child{margin-top:0}
input[type=search],input[type=number],select{width:100%;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);font:inherit}
.row{display:flex;gap:8px}
.seg{display:flex;flex-wrap:wrap;gap:6px}
.seg button{border:1px solid var(--line);background:var(--chip);color:var(--ink);border-radius:999px;padding:5px 11px;font:inherit;font-size:13px;cursor:pointer}
.seg button.on{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
label.chk{display:flex;gap:8px;align-items:center;font-size:14px;margin:4px 0;cursor:pointer}
.reset{margin-top:16px;width:100%;padding:8px;border-radius:8px;border:1px solid var(--line);background:none;color:var(--muted);cursor:pointer;font:inherit}
.bar{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;gap:12px;flex-wrap:wrap}
.count{font-weight:600}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px 16px;display:flex;flex-direction:column;gap:6px;position:relative}
.card.fav{border-color:var(--star)}
.price{font-size:22px;font-weight:700;letter-spacing:-.01em}
.specs{color:var(--muted);font-size:14px}
.ttl{font-weight:600;line-height:1.3}
.addr{font-size:13px;color:var(--muted)}
.tags{display:flex;flex-wrap:wrap;gap:5px;margin-top:2px}
.tag{font-size:12px;background:var(--chip);border-radius:999px;padding:2px 8px}
.tag.new{background:var(--new);color:#fff;font-weight:600}
.foot{display:flex;justify-content:space-between;align-items:center;margin-top:auto;padding-top:8px}
.foot a{color:var(--accent);font-weight:600;text-decoration:none}
.icons button{background:none;border:none;cursor:pointer;font-size:17px;padding:2px 4px;opacity:.55}
.icons button:hover,.icons button.on{opacity:1}
.empty{color:var(--muted);padding:40px 0;text-align:center}
details{margin-top:28px;color:var(--muted);font-size:13px}
details table{border-collapse:collapse;margin-top:8px}
details td{padding:3px 12px 3px 0;vertical-align:top}
#filtersToggle{display:none}
@media (max-width:760px){
  .wrap{grid-template-columns:1fr}
  aside{position:static;display:none}
  aside.open{display:block}
  #filtersToggle{display:inline-block;border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:8px;padding:6px 12px;font:inherit}
}
</style>
</head>
<body>
<header>
  <h1>__TITLE__</h1>
  <div class="sub">__SUBTITLE__ · updated <span id="gen"></span></div>
</header>
<div class="wrap">
  <aside id="filters">
    <h3>Search</h3>
    <input type="search" id="q" placeholder="Street, building, keyword…">
    <h3>Price</h3>
    <div class="row"><input type="number" id="pmin" placeholder="Min" step="50"><input type="number" id="pmax" placeholder="Max" step="50"></div>
    <h3>Beds</h3>
    <div class="seg" id="beds"></div>
    <h3>Baths</h3>
    <div class="seg" id="baths"></div>
    <h3>Pets</h3>
    <div class="seg" id="pets"></div>
    <h3>Source</h3>
    <div id="sources"></div>
    <h3>Show</h3>
    <label class="chk"><input type="checkbox" id="onlyNew"> New since last run</label>
    <label class="chk"><input type="checkbox" id="onlyFav"> ⭐ Favorites only</label>
    <label class="chk"><input type="checkbox" id="showHidden"> Show hidden</label>
    <label class="chk"><input type="checkbox" id="unknownPrice" checked> Include “price unknown”</label>
    <button class="reset" id="reset">Reset filters</button>
  </aside>
  <main>
    <div class="bar">
      <span class="count" id="count"></span>
      <span class="row" style="align-items:center">
        <button id="filtersToggle">Filters</button>
        <select id="sort" style="width:auto">
          <option value="price">Price: low → high</option>
          <option value="-price">Price: high → low</option>
          <option value="new">Newest first</option>
          <option value="beds">Most beds</option>
        </select>
      </span>
    </div>
    <div class="grid" id="grid"></div>
    <details><summary>Sources status</summary><table id="status"></table></details>
  </main>
</div>
<script id="data" type="application/json">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const L = DATA.listings.map((l, i) => ({...l, id: l.url + '|' + l.title}));
const store = {
  get(k, d){ try { return JSON.parse(localStorage.getItem(k)) ?? d } catch { return d } },
  set(k, v){ try { localStorage.setItem(k, JSON.stringify(v)) } catch {} },
};
let favs = new Set(store.get('favs', [])), hidden = new Set(store.get('hidden', []));
const $ = id => document.getElementById(id);
const D = DATA.defaults || {};
const state = {beds: D.min_beds ?? null, baths: D.min_baths ?? null, pets: D.pets || 'any'};
const sources = [...new Set(L.flatMap(l => l.source.split(', ')))].sort();

function seg(id, opts, key){
  const el = $(id);
  el.innerHTML = opts.map(([v, t]) => `<button data-v="${v}">${t}</button>`).join('');
  const paint = () => el.querySelectorAll('button').forEach(b => b.classList.toggle('on', String(state[key]) === b.dataset.v));
  el.onclick = e => { const b = e.target.closest('button'); if (!b) return;
    state[key] = b.dataset.v === 'null' ? null : (key === 'pets' ? b.dataset.v : +b.dataset.v); paint(); render(); };
  paint(); return paint;
}
const paints = [
  seg('beds', [['null','Any'],['0','Studio+'],['1','1+'],['2','2+'],['3','3+']], 'beds'),
  seg('baths', [['null','Any'],['1','1+'],['1.5','1.5+'],['2','2+']], 'baths'),
  seg('pets', [['any','Any'],['cats','Cats OK'],['dogs','Dogs OK']], 'pets'),
];
$('sources').innerHTML = sources.map(s => `<label class="chk"><input type="checkbox" class="src" value="${esc(s)}" checked> ${esc(s)}</label>`).join('');
function applyDefaults(){
  $('pmin').value = D.min_price ?? ''; $('pmax').value = D.max_price ?? '';
  state.beds = D.min_beds ?? null; state.baths = D.min_baths ?? null; state.pets = D.pets || 'any';
  $('q').value = ''; ['onlyNew','onlyFav','showHidden'].forEach(i => $(i).checked = false);
  $('unknownPrice').checked = true;
  document.querySelectorAll('.src').forEach(c => c.checked = true);
  paints.forEach(p => p());
}
function esc(s){ return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])) }
function petsOk(l){
  if (state.pets === 'any' || !l.pets) return true;
  const p = l.pets.toLowerCase(); if (p.includes('no pet')) return false;
  return p.includes(state.pets === 'cats' ? 'cat' : 'dog') || p.includes('pet');
}
function render(){
  const q = $('q').value.trim().toLowerCase();
  const pmin = parseFloat($('pmin').value), pmax = parseFloat($('pmax').value);
  const srcOn = new Set([...document.querySelectorAll('.src:checked')].map(c => c.value));
  let out = L.filter(l => {
    if (l.price == null) { if (!$('unknownPrice').checked) return false; }
    else { if (!isNaN(pmin) && l.price < pmin) return false; if (!isNaN(pmax) && l.price > pmax) return false; }
    if (state.beds != null && l.beds != null && l.beds < state.beds) return false;
    if (state.baths != null && l.baths != null && l.baths < state.baths) return false;
    if (!petsOk(l)) return false;
    if (!l.source.split(', ').some(s => srcOn.has(s))) return false;
    if ($('onlyNew').checked && !l.is_new) return false;
    if ($('onlyFav').checked && !favs.has(l.id)) return false;
    if (!$('showHidden').checked && hidden.has(l.id)) return false;
    if (q && !(l.title + ' ' + l.address + ' ' + l.source).toLowerCase().includes(q)) return false;
    return true;
  });
  const s = $('sort').value, big = 1e9;
  out.sort({
    'price': (a,b) => (a.price ?? big) - (b.price ?? big),
    '-price': (a,b) => (b.price ?? -1) - (a.price ?? -1),
    'new': (a,b) => (b.is_new - a.is_new) || String(b.posted_date || b.first_seen).localeCompare(a.posted_date || a.first_seen),
    'beds': (a,b) => (b.beds ?? -1) - (a.beds ?? -1) || (a.price ?? big) - (b.price ?? big),
  }[s]);
  $('count').textContent = `${out.length} of ${L.length} listings`;
  $('grid').innerHTML = out.length ? out.map(card).join('') : '<div class="empty">No listings match these filters.</div>';
}
function num(v){ return v == null ? null : (Number.isInteger(v) ? v : +v.toFixed(1)) }
function card(l){
  const specs = [l.beds == null ? null : (l.beds === 0 ? 'Studio' : num(l.beds) + ' bd'),
                 l.baths == null ? null : num(l.baths) + ' ba',
                 l.sqft ? l.sqft.toLocaleString() + ' sqft' : null].filter(Boolean).join(' · ');
  const showAddr = l.address && !l.title.toLowerCase().includes(l.address.toLowerCase());
  const tags = [l.is_new ? '<span class="tag new">NEW</span>' : '',
                ...l.source.split(', ').map(s => `<span class="tag">${esc(s)}</span>`),
                l.pets ? `<span class="tag">🐾 ${esc(l.pets)}</span>` : ''].join('');
  const f = favs.has(l.id), h = hidden.has(l.id);
  return `<div class="card${f ? ' fav' : ''}" style="${h ? 'opacity:.5' : ''}">
    <div class="price">${l.price ? '$' + l.price.toLocaleString() : 'Price n/a'}</div>
    ${specs ? `<div class="specs">${specs}</div>` : ''}
    <div class="ttl">${esc(l.title)}</div>
    ${showAddr ? `<div class="addr">${esc(l.address)}</div>` : ''}
    <div class="tags">${tags}</div>
    <div class="foot"><a href="${esc(l.url)}" target="_blank" rel="noopener">View listing →</a>
      <span class="icons">
        <button title="Favorite" class="${f ? 'on' : ''}" data-act="fav" data-id="${esc(l.id)}">${f ? '⭐' : '☆'}</button>
        <button title="${h ? 'Unhide' : 'Hide'}" class="${h ? 'on' : ''}" data-act="hide" data-id="${esc(l.id)}">${h ? '↩' : '🗑'}</button>
      </span></div>
  </div>`;
}
$('grid').onclick = e => {
  const b = e.target.closest('button[data-act]'); if (!b) return;
  const set = b.dataset.act === 'fav' ? favs : hidden, id = b.dataset.id;
  set.has(id) ? set.delete(id) : set.add(id);
  store.set('favs', [...favs]); store.set('hidden', [...hidden]); render();
};
['q','pmin','pmax'].forEach(i => $(i).addEventListener('input', render));
['sort','onlyNew','onlyFav','showHidden','unknownPrice'].forEach(i => $(i).addEventListener('change', render));
$('sources').addEventListener('change', render);
$('reset').onclick = () => { applyDefaults(); render(); };
$('filtersToggle').onclick = () => $('filters').classList.toggle('open');
$('gen').textContent = DATA.generated;
$('status').innerHTML = Object.entries(DATA.status).map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(v)}</td></tr>`).join('');
applyDefaults(); render();
</script>
</body>
</html>
"""
