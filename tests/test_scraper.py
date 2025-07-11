from types import SimpleNamespace
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'aggression_analyzer'))

import types

fake_modules = types.ModuleType('snscrape.modules')
fake_twitter = types.ModuleType('snscrape.modules.twitter')
fake_modules.twitter = fake_twitter
sys.modules['snscrape.modules'] = fake_modules
sys.modules['snscrape.modules.twitter'] = fake_twitter

from aggression_analyzer.modules.scraper import Scraper
import time


class FakeTweet(SimpleNamespace):
    pass


class FakeUserScraper:
    def __init__(self, username):
        self.username = username
        self.entity = SimpleNamespace(
            id=123,
            username=username,
            displayname="User",
            description="desc",
            followersCount=10,
            friendsCount=5,
        )

    def get_items(self):
        tweets = [
            FakeTweet(date='2024-01-01', url='https://x.com/1', content='a'),
            FakeTweet(date='2024-01-02', url='https://x.com/2', content='b'),
            FakeTweet(date='2024-01-03', url='https://x.com/3', content='c'),
        ]
        for t in tweets:
            yield t

fake_twitter.TwitterUserScraper = FakeUserScraper


def test_scrape_user_posts(monkeypatch):
    monkeypatch.setattr(
        'aggression_analyzer.modules.scraper.sntwitter.TwitterUserScraper',
        FakeUserScraper,
    )
    monkeypatch.setattr(
        'aggression_analyzer.modules.scraper.time.sleep',
        lambda _: None,
    )
    scraper = Scraper()
    df = scraper.scrape_user_posts('user', limit=2)
    assert len(df) == 2
    assert list(df.columns) == ['date', 'url', 'content']
    assert df.iloc[0]['content'] == 'a'
    assert df.iloc[1]['url'] == 'https://x.com/2'


def test_get_user_profile(monkeypatch):
    monkeypatch.setattr(
        'aggression_analyzer.modules.scraper.sntwitter.TwitterUserScraper',
        FakeUserScraper,
    )
    scraper = Scraper()
    profile = scraper.get_user_profile('user')
    assert profile and profile['username'] == 'user'
