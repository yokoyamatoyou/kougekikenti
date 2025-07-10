import os
import sys
import pandas as pd
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'aggression_analyzer'))

import pytest

from aggression_analyzer.modules.analyzer import Analyzer


class FakeChat:
    class Completions:
        @staticmethod
        def create(**kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='{"score": 7, "reason": "mocked"}'))]
            )

    completions = Completions()


class FakeOpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.chat = FakeChat()


def test_get_aggressiveness_score(monkeypatch):
    monkeypatch.setattr('aggression_analyzer.modules.analyzer.OpenAI', FakeOpenAI)
    analyzer = Analyzer(api_key='test')
    score, reason = analyzer.get_aggressiveness_score('hello')
    assert score == 7
    assert reason == 'mocked'


def test_analyze_dataframe_in_parallel(monkeypatch):
    analyzer = Analyzer(api_key='test')

    def fake_moderate_text(text: str):
        categories = SimpleNamespace(
            hate=False,
            hate_threatening=False,
            self_harm=False,
            sexual=False,
            sexual_minors=False,
            violence=False,
            violence_graphic=False,
        )
        scores = SimpleNamespace(
            hate=0.1,
            hate_threatening=0.2,
            self_harm=0.0,
            sexual=0.0,
            sexual_minors=0.0,
            violence=0.0,
            violence_graphic=0.0,
        )
        return categories, scores

    monkeypatch.setattr(analyzer, "moderate_text", fake_moderate_text)
    monkeypatch.setattr(analyzer, "get_aggressiveness_score", lambda text: (5, "ok"))

    df = pd.DataFrame({"content": ["a", "b", "c"]})
    progress = []

    def cb(done: int, total: int):
        progress.append(done)

    result = analyzer.analyze_dataframe_in_parallel(df, cb)

    assert list(progress) == [1, 2, 3]
    assert list(result["aggressiveness_score"]) == [5, 5, 5]
    assert "total_aggression" in result.columns
