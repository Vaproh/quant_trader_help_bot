import requests
from typing import List, Dict, Optional

from google import genai

from utils.logger import get_logger
from storage.cache import Cache
from config.constants import (
    API_TIMEOUT,
    API_RETRIES,
    CACHE_NEWS_TTL,
    NEWS_FETCH_INTERVAL
)
from utils.time_utils import now_ts, is_expired


logger = get_logger(__name__)


class NewsAnalyzer:

    def __init__(
        self,
        news_api_key: str,
        ai_api_key: str,
        cache: Optional[Cache] = None
    ):
        self.news_api_key = news_api_key
        self.ai_api_key = ai_api_key
        self.cache = cache or Cache()

        # Gemini setup
        self.client = genai.Client(api_key=self.ai_api_key)

        self._last_fetch_time = 0

    # =========================
    # 📰 FETCH NEWS
    # =========================
    def fetch_news(self, query: str = "crypto") -> List[str]:

        cache_key = f"news:{query}"

        cached = self.cache.get(cache_key)
        if cached:
            logger.debug("News cache HIT")
            return cached

        # Rate limit protection
        if not is_expired(self._last_fetch_time, NEWS_FETCH_INTERVAL):
            logger.debug("News fetch skipped (rate limit)")
            return []

        for attempt in range(API_RETRIES):
            try:
                url = (
                    f"https://newsapi.org/v2/everything?"
                    f"q={query}&pageSize=5&sortBy=publishedAt&apiKey={self.news_api_key}"
                )

                res = requests.get(url, timeout=API_TIMEOUT)

                if res.status_code != 200:
                    logger.warning(f"News API bad response: {res.status_code}")
                    continue

                data = res.json()
                articles = data.get("articles", [])

                headlines = [
                    a.get("title")
                    for a in articles
                    if a.get("title")
                ]

                # Cache result
                self.cache.set(cache_key, headlines, CACHE_NEWS_TTL)
                self._last_fetch_time = now_ts()

                return headlines

            except requests.exceptions.RequestException as e:
                logger.warning(f"News fetch error (attempt {attempt+1}): {e}")

            except Exception as e:
                logger.error(f"News unexpected error: {e}")

        logger.error("Failed to fetch news")
        return []

    # =========================
    # 🧠 GEMINI ANALYSIS
    # =========================
    def analyze(self, headlines: List[str]) -> Dict:

        if not headlines:
            return self._fallback("No headlines")

        if self.cache.get("ai_cooldown"):
            logger.warning("AI cooldown active → skipping Gemini")
            return self._fallback("Cooldown active")

        try:
            prompt = self._build_prompt(headlines)

            response = self.client.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=prompt
            )

            text = response.text

            if not text:
                return self._fallback("Empty AI response")

            return self._parse(text)

        except Exception as e:
            logger.error(f"Gemini error: {e}")

            self.cache.set("ai_cooldown", True, 60)

            return self._fallback("Gemini failed")

    # =========================
    # 🧠 FULL PIPELINE
    # =========================
    def get_sentiment(self, query: str = "crypto") -> Dict:

        cache_key = f"sentiment:{query}"

        cached = self.cache.get(cache_key)
        if cached:
            return cached

        headlines = self.fetch_news(query)

        result = self.analyze(headlines)

        self.cache.set(cache_key, result, CACHE_NEWS_TTL)

        return result

    # =========================
    # 🧠 PROMPT
    # =========================
    def _build_prompt(self, headlines: List[str]) -> str:

        news_text = "\n".join(headlines)

        return f"""
You are a crypto market analyst.

Analyze the sentiment of these headlines:

{news_text}

Return clearly:

Sentiment: BULLISH or BEARISH or NEUTRAL
Confidence: number between 0 and 100
Summary: short explanation
"""

    # =========================
    # 🔍 PARSER (ROBUST)
    # =========================
    def _parse(self, text: str) -> Dict:

        try:
            sentiment = "NEUTRAL"
            confidence = 50
            summary = text.strip()

            text_lower = text.lower()

            if "bull" in text_lower:
                sentiment = "BULLISH"
            elif "bear" in text_lower:
                sentiment = "BEARISH"

            # Extract confidence number
            import re
            match = re.search(r"\b([0-9]{1,3})\b", text)

            if match:
                confidence = max(0, min(100, int(match.group(1))))

            return {
                "sentiment": sentiment,
                "confidence": confidence,
                "summary": summary[:200]
            }

        except Exception as e:
            logger.error(f"Parse error: {e}")
            return self._fallback("Parse failed")

    # =========================
    # 🔁 FALLBACK
    # =========================
    def _fallback(self, reason: str) -> Dict:
        return {
            "sentiment": "NEUTRAL",
            "confidence": 40,
            "summary": f"Fallback: {reason}"
        }