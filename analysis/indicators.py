# analysis/indicators.py

from typing import List, Optional

from utils.logger import get_logger


logger = get_logger(__name__)


class Indicators:

    # =========================
    # 📈 EMA
    # =========================
    @staticmethod
    def ema(prices: List[float], period: int) -> float:
        try:
            if not prices or len(prices) < period:
                return 0.0

            k = 2 / (period + 1)
            ema_val = prices[0]

            for price in prices[1:]:
                ema_val = price * k + ema_val * (1 - k)

            return ema_val

        except Exception as e:
            logger.error(f"EMA error: {e}")
            return 0.0

    # =========================
    # 📉 RSI
    # =========================
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> float:
        try:
            if len(prices) < period + 1:
                return 50.0

            gains = []
            losses = []

            for i in range(1, period + 1):
                delta = prices[-i] - prices[-i - 1]

                if delta > 0:
                    gains.append(delta)
                else:
                    losses.append(abs(delta))

            avg_gain = sum(gains) / period if gains else 0
            avg_loss = sum(losses) / period if losses else 0

            if avg_loss == 0:
                return 100.0

            rs = avg_gain / avg_loss
            return 100 - (100 / (1 + rs))

        except Exception as e:
            logger.error(f"RSI error: {e}")
            return 50.0

    # =========================
    # 📊 SMA
    # =========================
    @staticmethod
    def sma(prices: List[float], period: int) -> float:
        try:
            if len(prices) < period:
                return 0.0

            return sum(prices[-period:]) / period

        except Exception as e:
            logger.error(f"SMA error: {e}")
            return 0.0

    # =========================
    # 📊 VOLATILITY
    # =========================
    @staticmethod
    def volatility(prices: List[float]) -> float:
        try:
            if not prices:
                return 0.0

            high = max(prices)
            low = min(prices)

            if low == 0:
                return 0.0

            return (high - low) / low

        except Exception as e:
            logger.error(f"Volatility error: {e}")
            return 0.0

    # =========================
    # 📊 TREND DETECTION
    # =========================
    @staticmethod
    def trend(prices: List[float]) -> str:
        try:
            if len(prices) < 50:
                return "NEUTRAL"

            ema_20 = Indicators.ema(prices[-50:], 20)
            ema_50 = Indicators.ema(prices[-50:], 50)

            if ema_20 > ema_50:
                return "UPTREND"
            elif ema_20 < ema_50:
                return "DOWNTREND"
            else:
                return "NEUTRAL"

        except Exception as e:
            logger.error(f"Trend error: {e}")
            return "NEUTRAL"

    # =========================
    # 📊 MOMENTUM SCORE
    # =========================
    @staticmethod
    def momentum(prices: List[float]) -> float:
        try:
            if len(prices) < 10:
                return 0.0

            return (prices[-1] - prices[-10]) / prices[-10] * 100

        except Exception as e:
            logger.error(f"Momentum error: {e}")
            return 0.0