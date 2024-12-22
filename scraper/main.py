import logging
from dataclasses import dataclass, field

import urllib3

# import boomkat
from boomkat import BoomkatChart, BoomkatScraper

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# TODO understand why it doesn't trust boomkat certificate
urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)


@dataclass
class Title:
    name: str
    charts: list[str] = field(default_factory=list)


@dataclass
class Artist:
    name: str
    titles: dict[str, Title] = field(default_factory=dict)


@dataclass
class Release:
    artist: str
    title: str
    charts: list[str] = field(default_factory=list)

    def appearances(self) -> int:
        return len(self.charts)


def _group_by_artist(charts: list[BoomkatChart]) -> dict[str, Artist]:
    # artists = defaultdict(Artist)
    artists = {}
    for chart in charts:
        for item in chart.items:
            artist_lower = item.artist.lower()
            title_lower = item.title.lower()
            if artist_lower not in artists:
                artists[artist_lower] = Artist(
                    name=item.artist,
                )
            if title_lower not in artists[artist_lower].titles:
                artists[artist_lower].titles[title_lower] = Title(
                    name=item.title,
                )
            artists[artist_lower].titles[title_lower].charts.append(chart.name)
    return artists


def _flatten_to_releases(artists: dict[str, Artist]) -> list[Release]:
    releases = []
    for artist_lower, artist in artists.items():
        for title_lower, title in artist.titles.items():
            releases.append(
                Release(
                    artist=artist.name,
                    title=title.name,
                    charts=title.charts,
                )
            )
    return releases


if __name__ == "__main__":
    scraper = BoomkatScraper()
    charts = scraper.scrape()
    artists = _group_by_artist(charts)
    releases = _flatten_to_releases(artists)

    popular_releases = sorted(releases, key=lambda x: x.appearances(), reverse=True)
    for release in popular_releases[0:10]:
        logger.info(
            f'"{release.artist} - {release.title}" appears in {release.appearances()} charts'
        )
