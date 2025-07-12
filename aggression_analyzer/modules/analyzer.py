import os
import json
import time
import logging
from typing import Any, Callable, Optional

import pandas as pd
from openai import OpenAI

from config.settings import (
    MODERATION_MODEL,
    AGGRESSION_ANALYSIS_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    AGGRESSION_PROMPT_TEMPLATE,
    WEIGHTS,
    MAX_CONCURRENT_WORKERS,
)


class Analyzer:
    def __init__(self, api_key: str | None = None) -> None:
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        if self.client.api_key is None:
            raise ValueError("OpenAI APIキーが設定されていません。")
        self.temperature = DEFAULT_TEMPERATURE
        self.top_p = DEFAULT_TOP_P

    def moderate_text(self, text: str) -> tuple[Any, Any]:
        response = self.client.moderations.create(
            input=text,
            model=MODERATION_MODEL,
        )
        categories = response.results[0].categories
        scores = response.results[0].category_scores
        return categories, scores

    def get_aggressiveness_score(
        self, text: str, max_retries: int = 3
    ) -> tuple[int | None, str | None]:
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
                print(
                    f"エラーが発生しました（試行 {attempt + 1}/{max_retries}）: {e}"
                )
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
            + WEIGHTS.get("hate_flag", 2.0)
            * (1 if row.get("hate_flag") else 0)
            + WEIGHTS.get("hate/threatening_flag", 1.0)
            * (1 if row.get("hate/threatening_flag") else 0)
            + WEIGHTS.get("violence_flag", 1.5)
            * (1 if row.get("violence_flag") else 0)
            + WEIGHTS.get("sexual_flag", 1.0)
            * (1 if row.get("sexual_flag") else 0)
        )

    def analyze_dataframe_in_parallel(
        self,
        df: pd.DataFrame,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> pd.DataFrame:
        """Analyze a DataFrame using parallel threads.

        Each row is processed with :meth:`moderate_text` and
        :meth:`get_aggressiveness_score`.  Results are merged back into the
        original DataFrame. ``progress_callback`` is called after each row is
        processed with the current completed count and total count.
        """

        from concurrent.futures import ThreadPoolExecutor, as_completed

        category_names = [
            "hate",
            "hate/threatening",
            "self-harm",
            "sexual",
            "sexual/minors",
            "violence",
            "violence/graphic",
        ]

        def process_row(index: int, text: str) -> tuple[int, dict[str, Any]]:
            try:
                categories, scores = self.moderate_text(text)
                score, reason = self.get_aggressiveness_score(text)
            except Exception:
                logging.exception("Failed to process row %s", index)
                result: dict[str, Any] = {
                    "aggressiveness_score": None,
                    "aggressiveness_reason": None,
                }
                for name in category_names:
                    result[f"{name}_flag"] = False
                    result[f"{name}_score"] = 0.0
                return index, result

            result: dict[str, Any] = {
                "aggressiveness_score": score,
                "aggressiveness_reason": reason,
            }
            for name in category_names:
                flag = getattr(categories, name.replace("/", "_"), False)
                sc = getattr(scores, name.replace("/", "_"), 0.0)
                result[f"{name}_flag"] = flag
                result[f"{name}_score"] = sc
            return index, result

        results: dict[int, dict[str, Any]] = {}
        total = len(df)
        completed = 0
        with ThreadPoolExecutor(
            max_workers=MAX_CONCURRENT_WORKERS
        ) as executor:
            futures = {
                executor.submit(process_row, i, row["content"]): i
                for i, row in df.iterrows()
            }
            for future in as_completed(futures):
                index, data = future.result()
                results[index] = data
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)

        for index, data in results.items():
            for key, value in data.items():
                df.loc[index, key] = value
        df["total_aggression"] = df.apply(self.total_aggression, axis=1)
        return df
