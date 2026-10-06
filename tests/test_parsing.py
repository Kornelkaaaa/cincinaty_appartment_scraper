from scraper.dedupe import dedupe
from scraper.filters import apply_filters
from scraper.models import Listing, parse_baths, parse_beds, parse_price, parse_sqft
from scraper.sources.property_managers import parse_site
from scraper.state import mark_new


def test_parse_price():
    assert parse_price("$1,450/mo") == 1450
    assert parse_price("$1,200 - $1,600") == 1200
    assert parse_price("1295") == 1295
    assert parse_price("Call for pricing") is None


def test_parse_beds_baths_sqft():
    assert parse_beds("Studio") == 0
    assert parse_beds("2 bd") == 2
    assert parse_beds("1-2 Beds") == 1
    assert parse_beds("3br") == 3
    assert parse_baths("1.5 ba") == 1.5
    assert parse_sqft("850ft2") == 850
    assert parse_sqft("1,100 sq ft") == 1100


def L(**kw):
    base = dict(source="t", title="Nice apt", url="https://x/1")
    base.update(kw)
    return Listing(**base)


def test_filters():
    f = {"min_price": 900, "max_price": 1500, "min_beds": 1, "min_baths": None,
         "pets": "dogs", "exclude_keywords": ["sublet"]}
    keep = L(price=1200, beds=1)
    unknown = L(url="https://x/u")  # unknown values are kept
    out = apply_filters([
        keep, unknown,
        L(price=1800), L(beds=0), L(title="Summer sublet"), L(pets="cats"), L(pets="no pets"),
    ], f)
    assert out == [keep, unknown]


def test_dedupe_by_address():
    a = L(source="Zillow", url="https://z/1", address="3000 Madison Road, Cincinnati, OH", price=1300, beds=1)
    b = L(source="Craigslist", url="https://c/1", address="3000 Madison Rd", price=1300, beds=1, sqft=700)
    out = dedupe([a, b])
    assert len(out) == 1
    assert out[0].sqft == 700 and "Zillow" in out[0].source and "Craigslist" in out[0].source


def test_mark_new(tmp_path):
    state = tmp_path / "seen.json"
    first = [L(url="https://x/1")]
    mark_new(first, state)
    assert not first[0].is_new  # first run: nothing flagged
    second = [L(url="https://x/1"), L(url="https://x/2")]
    mark_new(second, state)
    assert [l.is_new for l in second] == [False, True]


def test_property_manager_selectors():
    html = """
    <div class="fp"><h3>The Ash</h3><span class="rent">$1,350</span><span class="bd">1 Bed</span>
      <a href="/fp/ash">Details</a></div>
    <div class="fp"><h3>The Oak</h3><span class="rent">Starting at $1,795</span><span class="bd">2 Beds</span></div>
    """
    site = {"name": "Oakley Flats", "url": "https://oakleyflats.example/floorplans",
            "selectors": {"card": ".fp", "title": "h3", "price": ".rent", "beds": ".bd", "link": "a"}}
    out = parse_site(html, site)
    assert [(l.price, l.beds) for l in out] == [(1350, 1), (1795, 2)]
    assert out[0].url == "https://oakleyflats.example/fp/ash"
