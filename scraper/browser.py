"""Playwright helper for JS-heavy / bot-protected sites."""
from __future__ import annotations

import logging
import random
import time
from contextlib import contextmanager

from .http import USER_AGENT

log = logging.getLogger("scraper.browser")


class BlockedError(RuntimeError):
    """Raised when a site serves a captcha / access-denied page."""


BLOCK_MARKERS = (
    "press & hold",
    "px-captcha",
    "are you a human",
    "access denied",
    "access to this page has been denied",
    "verify you are human",
)


@contextmanager
def browser_page(headless: bool = True):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:  # pragma: no cover
        raise RuntimeError(
            "Playwright not installed: pip install playwright && playwright install chromium"
        ) from e
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless, args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1366, "height": 900},
            locale="en-US",
        )
        page = context.new_page()
        page.set_default_timeout(30000)
        try:
            yield page
        finally:
            context.close()
            browser.close()


def _is_blocked(html: str) -> bool:
    lowered = html.lower()
    return any(marker in lowered for marker in BLOCK_MARKERS) and len(lowered) < 200_000


def goto(
    page,
    url: str,
    delay_range=(2, 5),
    wait_for: str | None = None,
    captcha_wait: int = 0,
) -> str:
    """Navigate, wait a human-ish amount, check for blocks, return HTML.

    With a visible browser (captcha_wait > 0) the user gets that many seconds to
    solve a captcha by hand before we give up.
    """
    page.goto(url, wait_until="domcontentloaded")
    if wait_for:
        try:
            page.wait_for_selector(wait_for, timeout=15000)
        except Exception:
            pass
    time.sleep(random.uniform(*delay_range))
    html = page.content()
    if _is_blocked(html) and captcha_wait > 0:
        log.warning("Captcha at %s – solve it in the browser window (%ds)...", url, captcha_wait)
        deadline = time.time() + captcha_wait
        while time.time() < deadline and _is_blocked(html):
            time.sleep(3)
            html = page.content()
        if wait_for and not _is_blocked(html):
            try:
                page.wait_for_selector(wait_for, timeout=15000)
            except Exception:
                pass
            html = page.content()
    if _is_blocked(html):
        raise BlockedError(
            f"Blocked by bot protection at {url} (try --show-browser and solve the captcha)"
        )
    return html
