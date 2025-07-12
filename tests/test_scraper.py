import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'aggression_analyzer'))

import types

fake_ntscraper = types.ModuleType('ntscraper')

class FakeNitter:
    def __init__(self, instances=None, skip_instance_check=False):
        pass

    def get_tweets(self, term, mode="user", number=20):
        if mode == "user" and term == "nouser":
            raise ValueError("user not found")
        if mode == "term" and term == "rarekeyword":
            return {"tweets": []}

        tweets = [
            {
                "date": "2024-01-01",
                "link": "https://x.com/1",
                "text": "a",
                "user": {"username": "user"},
            },
            {
                "date": "2024-01-02",
                "link": "https://x.com/2",
                "text": "b",
                "user": {"username": "user"},
            },
            {
                "date": "2024-01-03",
                "link": "https://x.com/3",
                "text": "c",
                "user": {"username": "user"},
            },
        ]
        return {"tweets": tweets[:number]}

    def get_profile_info(self, username):
        return {
            "id": 123,
            "username": username,
            "name": "User",
            "bio": "desc",
            "stats": {"followers": 10, "following": 5},
        }

fake_ntscraper.Nitter = FakeNitter
sys.modules['ntscraper'] = fake_ntscraper

from aggression_analyzer.modules.scraper import Scraper
import time


def test_scrape_user_posts(monkeypatch):
    calls: list[float] = []

    def fake_sleep(sec: float):
        calls.append(sec)

    monkeypatch.setattr('aggression_analyzer.modules.scraper.time.sleep', fake_sleep)
    scraper = Scraper()
    df = scraper.scrape_user_posts('user', limit=2)
    assert len(df) == 2
    assert list(df.columns) == ['timestamp', 'url', 'content', 'user_name']
    assert df.iloc[0]['content'] == 'a'
    assert df.iloc[1]['url'] == 'https://x.com/2'
    assert len(calls) == 1


def test_get_user_profile():
    scraper = Scraper()
    profile = scraper.get_user_profile('user')
    assert profile and profile['username'] == 'user'


def test_search_posts_by_keyword(monkeypatch):
    calls: list[float] = []

    def fake_sleep(sec: float):
        calls.append(sec)

    monkeypatch.setattr('aggression_analyzer.modules.scraper.time.sleep', fake_sleep)
    scraper = Scraper()
    df = scraper.search_posts_by_keyword('hello', limit=1)
    assert len(df) == 1
    assert df.iloc[0]['url'] == 'https://x.com/1'
    assert len(calls) == 1


def test_nonexistent_user_returns_empty_dataframe(monkeypatch):
    calls: list[float] = []

    def fake_sleep(sec: float):
        calls.append(sec)

    monkeypatch.setattr('aggression_analyzer.modules.scraper.time.sleep', fake_sleep)
    scraper = Scraper()
    df = scraper.scrape_user_posts('nouser', limit=1)
    assert df.empty
    assert list(df.columns) == ['timestamp', 'url', 'content', 'user_name']
    assert calls == []


def test_rare_keyword_returns_zero_results(monkeypatch):
    calls: list[float] = []

    def fake_sleep(sec: float):
        calls.append(sec)

    monkeypatch.setattr('aggression_analyzer.modules.scraper.time.sleep', fake_sleep)
    scraper = Scraper()
    df = scraper.search_posts_by_keyword('rarekeyword', limit=5)
    assert df.empty
    assert list(df.columns) == ['timestamp', 'url', 'content', 'user_name']
    assert len(calls) == 1


def test_search_dataframe_columns(monkeypatch):
    calls: list[float] = []

    def fake_sleep(sec: float):
        calls.append(sec)

    monkeypatch.setattr('aggression_analyzer.modules.scraper.time.sleep', fake_sleep)
    scraper = Scraper()
    df = scraper.search_posts_by_keyword('hello', limit=1)
    assert set(['timestamp', 'url', 'content', 'user_name']).issubset(df.columns)
    assert len(calls) == 1
