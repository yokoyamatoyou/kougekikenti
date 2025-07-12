from typing import Optional, List, Dict
import time
from config.settings import SCRAPE_DELAY_SECONDS
import pandas as pd
import requests

try:
    from ntscraper import Nitter
    SCRAPE_AVAILABLE = True
    SCRAPE_IMPORT_ERROR: Exception | None = None
except Exception as e:  # pragma: no cover - environment dependent
    SCRAPE_AVAILABLE = False
    SCRAPE_IMPORT_ERROR = e
    Nitter = None  # type: ignore


class Scraper:
    def __init__(self, instance: str | None = "https://nitter.net") -> None:
        self.instance = instance
        self._nitter = (
            self._create_nitter(instance) if SCRAPE_AVAILABLE else None
        )
        self._columns = ["timestamp", "url", "content", "user_name"]

    def _create_nitter(self, instance: str):
        """Return a configured :class:`Nitter` client."""
        return Nitter(instances=[instance], skip_instance_check=True)

    def _fetch_tweets(self, term: str, mode: str, limit: int) -> pd.DataFrame:
        if not SCRAPE_AVAILABLE:
            print(f"ntscraper not available: {SCRAPE_IMPORT_ERROR}")
            return pd.DataFrame(columns=self._columns)

        tweets: List[Dict[str, object]] = []
        try:
            data = self._nitter.get_tweets(term, mode=mode, number=limit)
            time.sleep(SCRAPE_DELAY_SECONDS)
            for item in data.get("tweets", []):
                tweets.append(
                    {
                        "timestamp": item.get("date"),
                        "url": item.get("link"),
                        "content": item.get("text"),
                        "user_name": item.get("user", {}).get("username"),
                    }
                )
        except Exception as e:
            print(f"{mode} error: {e}")
            return pd.DataFrame(columns=self._columns)
        return pd.DataFrame(tweets, columns=self._columns)

    def scrape_user_posts(
        self, username: str, limit: int = 20
    ) -> pd.DataFrame:
        """Scrape recent posts from an X (Twitter) user.

        Parameters
        ----------
        username:
            The user ID to scrape posts from.
        limit:
            Maximum number of posts to retrieve.

        Returns
        -------
        pandas.DataFrame
            Data frame containing ``timestamp``, ``url``, ``content`` and
            ``user_name`` columns. If scraping is unavailable or fails,
            an empty DataFrame is returned.
        """

        return self._fetch_tweets(username, "user", limit)

    def search_posts_by_keyword(
        self, keyword: str, limit: int = 20
    ) -> pd.DataFrame:
        """Search posts by keyword using Nitter."""

        return self._fetch_tweets(keyword, "term", limit)

    def get_user_profile(self, username: str) -> Optional[dict[str, object]]:
        """Fetch basic profile information for ``username``.

        Returns ``None`` when scraping is unavailable or fails."""

        if not SCRAPE_AVAILABLE:
            print(f"ntscraper not available: {SCRAPE_IMPORT_ERROR}")
            return None

        try:
            info = self._nitter.get_profile_info(username)
            if not info:
                return None
            return {
                "id": info.get("id"),
                "username": info.get("username"),
                "displayname": info.get("name"),
                "description": info.get("bio"),
                "followers": info.get("stats", {}).get("followers"),
                "following": info.get("stats", {}).get("following"),
            }
        except Exception as e:
            print(f"profile error: {e}")
            return None


def archive_url(url: str) -> str:
    """Create a web archive of ``url`` using the Wayback Machine."""

    try:
        response = requests.get(
            "https://web.archive.org/save/" + url,
            timeout=10,
        )
        if response.status_code in (200, 302):
            archive = response.headers.get("Content-Location")
            if archive:
                return "https://web.archive.org" + archive
    except Exception as e:
        print(f"archive error: {e}")
    return ""


if __name__ == "__main__":
    scraper = Scraper()
    df = scraper.scrape_user_posts("jack", 5)
    print(df.head())
