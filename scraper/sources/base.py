"""Base class for listing sources."""
from __future__ import annotations

import logging

from ..models import Listing


class Source:
    name = "base"

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.area = cfg["area"]
        self.max_pages = int(cfg["scraping"]["max_pages"])
        self.delay = tuple(cfg["scraping"]["delay_seconds"])
        self.headless = bool(cfg["scraping"]["headless"])
        # Seconds to wait for a human to solve a captcha (only with a visible browser).
        self.captcha_wait = 0 if self.headless else int(cfg["scraping"].get("captcha_wait", 120))
        self.log = logging.getLogger(f"scraper.{self.name}")

    def scrape(self) -> list[Listing]:
        raise NotImplementedError
