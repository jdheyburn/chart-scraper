import logging

import requests

logger = logging.getLogger(__name__)


_CACHE_DIR = ".cache"


class Scraper:
    def __init__(self, url: str):
        self.url = url

    def _get_cache_path(self, url: str) -> str:
        return f"{_CACHE_DIR}/{url.replace('/', '_')}"

    def _get_cached(self, url: str) -> str:
        cache_path = self._get_cache_path(url)
        try:
            with open(cache_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            return None

    def _cache(self, url: str, content: str):
        cache_path = self._get_cache_path(url)
        with open(cache_path, "w") as f:
            f.write(content)

    def _get_with_cache(self, url: str) -> str:
        cached = self._get_cached(url)
        if cached:
            logger.debug(f"Using cached content for {url}")
            return cached
        response = requests.get(url, verify=False)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch {url}")
        content = response.text
        logger.debug(f"Caching content for {url}")
        self._cache(url, content)
        return content
