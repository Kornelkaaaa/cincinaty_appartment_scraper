# Oakley (Cincinnati) Apartment Scraper

Collects apartment rentals in Oakley, Cincinnati (ZIP 45209) from **Craigslist**, **Zillow**, **Apartments.com** and **local property-manager sites**. It filters them using `config.yaml` and writes a Markdown report (`listings.md`), flagging listings that are new since the last run.

## Setup
```bash
pip install -r requirements.txt
python -m playwright install chromium
```

## Usage
```bash
python main.py                                # all sources enabled in config.yaml
python main.py --sources craigslist           # one source
python main.py --sources zillow,apartments_com --show-browser   # visible browser, solve captchas by hand
python main.py --out oakley.md -v
```
Sources: `craigslist`, `zillow`, `apartments_com`, `property_managers`.

## Configuration (`config.yaml`)
- `filters`: `min_price`, `max_price`, `min_beds` (0 = studios OK), `min_baths`, `pets` (`any|cats|dogs`), `exclude_keywords`. Listings missing a value (e.g. no pet info) are **kept**, not dropped.
- `area`: ZIP, neighborhood and Craigslist search radius.
- `scraping`: pages per source, delay between requests, headless/visible browser, captcha wait.
- `sources.property_managers`: add your own Oakley complexes. Each entry needs the page URL that lists units/floorplans, plus CSS selectors for one unit card (`card`, `title`, `price`, `beds`, `baths`, `sqft`, `link`). To find them, open the page in Chrome, right-click a unit, choose *Inspect*, and copy the class names. Set `browser: true` if the units load via JavaScript (most RentCafe/Entrata sites do).

## Output
- `listings.html`: a filterable web page (price, beds, baths, pets, source, search, sort). Favorites ⭐ and hidden 🗑 listings are remembered in your browser.
`listings.md` contains a sources status table (including failures), a "🆕 New since last run" section, and all matching listings sorted by price. `seen.json` remembers listings between runs, so delete it to reset "new" tracking.

## Scheduled runs (GitHub Actions)
`.github/workflows/scrape.yml` runs at 7:00 and 17:00 Cincinnati time and keeps `seen.json` in the Actions cache so "NEW" badges work. To trigger it by hand: Actions tab → *Scrape listings* → *Run workflow*.

### Shareable link (one-time setup)
Each run publishes the page to a separate **public** repo, so this repo can stay private. The link is `https://kornelkaaaa.github.io/oakley-listings/`. The page asks search engines not to index it.

1. Create a new **public** repo named `oakley-listings`. It can be empty.
2. Create a token: GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate. Under *Repository access*, choose *Only select repositories* → `oakley-listings`. Under *Permissions → Contents*, choose **Read and write**.
3. In **this** repo: Settings → Secrets and variables → Actions → *New repository secret*. Name it `PAGES_TOKEN` and paste the token.
4. Actions → *Scrape listings* → *Run workflow*.
5. In `oakley-listings`: Settings → Pages → *Deploy from a branch* → `gh-pages` / `(root)` → Save. After a minute or two the link works.

Until `PAGES_TOKEN` is set, the page is still uploaded as a downloadable artifact on each run (Actions → run → Artifacts). The token expires on the date you chose, so make a new one then.

The scheduled run uses Craigslist and your property-manager sites only, because Zillow and Apartments.com block GitHub's servers. For those, run locally with `--show-browser`.

## Notes on reliability
- **Craigslist** works reliably with plain HTTP.
- **Zillow and Apartments.com** use aggressive bot protection (PerimeterX/Akamai). In headless mode they usually serve a captcha, which is reported as a failure in the report. Use `--show-browser` and solve the captcha in the window (you get `captcha_wait` seconds); after that the run continues.
- Be polite: run a few times a day at most. Respect each site's terms of use; this tool is for personal apartment hunting.

## Tests
```bash
python -m pytest -q
```
