# OpenAI Models
MODERATION_MODEL = "text-moderation-latest"
AGGRESSION_ANALYSIS_MODEL = "gpt-4o-mini"

# Concurrency Settings
# 同時に実行する分析タスク数の上限
MAX_CONCURRENT_WORKERS = 8

# Scraper Settings
# 1リクエストごとの待機秒数
SCRAPE_DELAY_SECONDS = 1

# Analysis Parameters
DEFAULT_TEMPERATURE = 0.5
DEFAULT_TOP_P = 1.0

# Aggression Score Weights
WEIGHTS = {
    "hate_score": 0.5,
    # ... other weights can be filled later
}

AGGRESSION_PROMPT_TEMPLATE = """
あなたはソーシャルメディアの投稿を分析し、その攻撃性を評価する専門家です。
以下の基準に従って、与えられた文章の攻撃性スコアを決定し、その理由を説明してください。

# 評価基準:
0: 攻撃性なし。
1-3: 軽度の攻撃性（例: 皮肉、無神経な表現）。
4-6: 中程度の攻撃性（例: 明確な批判、侮辱）。
7-9: 高度の攻撃性（例: 強い敵意、脅迫）。
10: 極度の攻撃性（例: 暴力の助長、深刻な人権侵害）。

# 分析対象の文章:
---
{text}
---

# 出力形式:
必ず以下のJSON形式で回答してください。
{{
  "score": [0-10の整数],
  "reason": "なぜそのスコアを付けたのかを40文字程度で具体的に説明"
}}
"""
