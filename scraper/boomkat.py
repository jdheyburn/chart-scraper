import logging
import re
from dataclasses import dataclass
from typing import Union

import bs4
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_CACHE_DIR = "../.cache"


@dataclass
class BoomkatRelease:
    artist: str
    title: str
    label: str
    link: str


@dataclass
class BoomkatChart:
    name: str
    url: str
    items: list[BoomkatRelease]


class BoomkatScraper:
    _BASE_URL: str = "https://boomkat.com"

    # Matches a title and label in the format "TITLE (LABEL)"
    _TITLE_LABEL_PATTERN: str = r"^(.*?)\s*(?:\((.*?)\))?$"

    def __init__(self):
        pass

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

    # write a series of functions to retrieve a url from the cache, or if it doesn't exist, fetch it from the internet
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

    def _get_charts_from_root(self) -> bs4.element.ResultSet:
        # TODO make root dynamic (i.e. query previous years)
        root = "/charts/boomkat-end-of-year-charts-2024"
        response = self._get_with_cache(f"{BoomkatScraper._BASE_URL}{root}")
        soup = BeautifulSoup(response, "html.parser")
        charts = soup.findAll("a", {"class": "charts-index-chart"})
        logger.info(f"found {len(charts)} charts")
        return charts

    def _extract_title_and_label(self, input_string: str) -> Union[str, str]:
        # Remove any newlines and leading/trailing whitespace
        input_string = input_string.replace("\n", " ").strip()
        # Remove first '-' or '–' and any leading/trailing whitespace
        input_string = input_string[1:].strip()
        # Remove any leading/trailing whitespace
        input_string = re.sub(" +", " ", input_string)
        # At this point, the title should be in the format "TITLE (LABEL)", (LABEL) is optional
        match = re.match(BoomkatScraper._TITLE_LABEL_PATTERN, input_string)
        if not match:
            return None, None
        title = match.group(1).strip()  # Extract TITLE
        label = (
            match.group(2).strip() if match.group(2) else None
        )  # Extract LABEL if it exists
        return title, label

    def _parse_chart_item(self, item: bs4.element.Tag) -> BoomkatRelease:
        chart_item_title = item.find("div", {"class": "chart-item-title"})
        artist = chart_item_title.strong.text
        link = chart_item_title.a["href"] if chart_item_title.a else None
        title, label = self._extract_title_and_label(
            chart_item_title.strong.next_sibling.replace("\n", " ").strip()
        )
        return BoomkatRelease(artist, title, label, link)

    def _scrape_chart(self, chart: bs4.element.Tag) -> list[BoomkatRelease]:
        chart_url = chart["href"]
        chart_name = chart.img["alt"].replace(" 2024", "")
        logger.info(f"Scraping chart: {chart_name} at {chart_url}")
        response = self._get_with_cache(f"{BoomkatScraper._BASE_URL}{chart_url}")
        soup = BeautifulSoup(response, "html.parser")
        chart_items_soup = soup.findAll("div", {"class": "chart-item"})
        chart_items = [self._parse_chart_item(item) for item in chart_items_soup]
        return BoomkatChart(chart_name, chart_url, chart_items)

    def scrape(self):
        charts_raw = self._get_charts_from_root()
        charts = [self._scrape_chart(chart) for chart in charts_raw]
        return charts
