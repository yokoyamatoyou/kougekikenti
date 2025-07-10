from typing import Optional
import time
from config.settings import SCRAPE_DELAY_SECONDS
import pandas as pd

try:
    import snscrape.modules.twitter as sntwitter
    SCRAPE_AVAILABLE = True
    SCRAPE_IMPORT_ERROR: Exception | None = None
except Exception as e:  # pragma: no cover - environment dependent
    SCRAPE_AVAILABLE = False
    SCRAPE_IMPORT_ERROR = e
    sntwitter = None  # type: ignore


class Scraper:
    def scrape_user_posts(self, username: str, limit: int = 20) -> pd.DataFrame:
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
            Data frame containing ``date``, ``url``, and ``content`` columns.
            If scraping is unavailable or fails, an empty DataFrame is returned.
        """

        if not SCRAPE_AVAILABLE:
            print(f"snscrape not available: {SCRAPE_IMPORT_ERROR}")
            return pd.DataFrame()

        tweets = []
        try:
            for i, tweet in enumerate(
                sntwitter.TwitterUserScraper(username).get_items()
            ):
                if i >= limit:
                    break
                tweets.append(
                    {
                        "date": tweet.date,
                        "url": tweet.url,
                        "content": tweet.content,
                    }
                )
                time.sleep(SCRAPE_DELAY_SECONDS)
        except Exception as e:
            print(f"scrape error: {e}")
            return pd.DataFrame()
        return pd.DataFrame(tweets)


if __name__ == "__main__":
    scraper = Scraper()
    df = scraper.scrape_user_posts("jack", 5)
    print(df.head())
