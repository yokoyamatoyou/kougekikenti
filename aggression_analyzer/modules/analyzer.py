import os
import json
import time
from typing import Tuple, List

import pandas as pd
from openai import OpenAI

from config.settings import (
    MODERATION_MODEL,
    AGGRESSION_ANALYSIS_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    AGGRESSION_PROMPT_TEMPLATE,
    WEIGHTS,
)


class Analyzer:
    def __init__(self, api_key: str | None = None) -> None:
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        if self.client.api_key is None:
            raise ValueError("OpenAI APIキーが設定されていません。")
        self.temperature = DEFAULT_TEMPERATURE
        self.top_p = DEFAULT_TOP_P

    def moderate_text(self, text: str):
        response = self.client.moderations.create(
            input=text,
            model=MODERATION_MODEL,
        )
        categories = response.results[0].categories
        scores = response.results[0].category_scores
        return categories, scores

    def get_aggressiveness_score(self, text: str, max_retries: int = 3) -> Tuple[int | None, str | None]:
        prompt = AGGRESSION_PROMPT_TEMPLATE.format(text=text)
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=AGGRESSION_ANALYSIS_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    top_p=self.top_p,
                    response_format={"type": "json_object"},
                )
                data = json.loads(response.choices[0].message.content)
                score = int(data.get("score"))
                reason = str(data.get("reason"))
                if 0 <= score <= 10:
                    return score, reason
            except Exception as e:
                print(f"エラーが発生しました（試行 {attempt + 1}/{max_retries}）: {e}")
            time.sleep(1)
        return None, None

    def total_aggression(self, row: pd.Series) -> float:
        """Calculate a composite aggression score for a dataframe row.

        Each category score and flag is multiplied by a weight defined in
        :data:`config.settings.WEIGHTS`.  When a weight is not present, the
        original constant used by this project is applied as a default.
        """

        return (
            WEIGHTS.get("hate_score", 0.5) * row.get("hate_score", 0)
            + WEIGHTS.get("hate/threatening_score", 0.3)
            * row.get("hate/threatening_score", 0)
            + WEIGHTS.get("violence_score", 0.3) * row.get("violence_score", 0)
            + WEIGHTS.get("sexual_score", 0.1) * row.get("sexual_score", 0)
            + WEIGHTS.get("sexual/minors_score", 0.1)
            * row.get("sexual/minors_score", 0)
            + WEIGHTS.get("aggressiveness_score", 0.5)
            * (row.get("aggressiveness_score") or 0)
            + WEIGHTS.get("hate_flag", 2.0) * (1 if row.get("hate_flag") else 0)
            + WEIGHTS.get("hate/threatening_flag", 1.0)
            * (1 if row.get("hate/threatening_flag") else 0)
            + WEIGHTS.get("violence_flag", 1.5)
            * (1 if row.get("violence_flag") else 0)
            + WEIGHTS.get("sexual_flag", 1.0)
            * (1 if row.get("sexual_flag") else 0)
        )
