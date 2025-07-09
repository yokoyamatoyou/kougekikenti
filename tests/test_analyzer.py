import os
import sys
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
