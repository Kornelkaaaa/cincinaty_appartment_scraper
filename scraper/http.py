"""Shared, polite HTTP session."""
from __future__ import annotations

import random
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class PoliteSession:
    def __init__(self, delay_range=(2, 5)):
        self.delay_range = delay_range
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        retry = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self._last = 0.0

    def get(self, url: str, **kwargs) -> requests.Response:
        wait = random.uniform(*self.delay_range) - (time.time() - self._last)
        if self._last and wait > 0:
            time.sleep(wait)
        try:
            resp = self.session.get(url, timeout=30, **kwargs)
        finally:
            self._last = time.time()
        resp.raise_for_status()
        return resp
