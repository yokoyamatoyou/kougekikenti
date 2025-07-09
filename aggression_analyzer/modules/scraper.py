from typing import Optional
import pandas as pd
import snscrape.modules.twitter as sntwitter


class Scraper:
    def scrape_user_posts(self, username: str, limit: int = 20) -> pd.DataFrame:
        tweets = []
        try:
            for i, tweet in enumerate(sntwitter.TwitterUserScraper(username).get_items()):
                if i >= limit:
                    break
                tweets.append({
                    "date": tweet.date,
                    "url": tweet.url,
                    "content": tweet.content,
                })
        except Exception as e:
            print(f"scrape error: {e}")
            return pd.DataFrame()
        return pd.DataFrame(tweets)


if __name__ == "__main__":
    scraper = Scraper()
    df = scraper.scrape_user_posts("jack", 5)
    print(df.head())
