from typing import List

from utils.logger import get_logger


logger = get_logger(__name__)


class Patterns:

    # =========================
    # 📈 HIGHER HIGHS (UPTREND STRUCTURE)
    # =========================
    @staticmethod
    def higher_highs(highs: List[float]) -> bool:
        try:
            if len(highs) < 3:
                return False

            return highs[-1] > highs[-2] > highs[-3]

        except Exception as e:
            logger.error(f"Higher highs error: {e}")
            return False

    # =========================
    # 📉 LOWER LOWS (DOWNTREND STRUCTURE)
    # =========================
    @staticmethod
    def lower_lows(lows: List[float]) -> bool:
        try:
            if len(lows) < 3:
                return False

            return lows[-1] < lows[-2] < lows[-3]

        except Exception as e:
            logger.error(f"Lower lows error: {e}")
            return False

    # =========================
    # 🔄 RANGE DETECTION
    # =========================
    @staticmethod
    def is_range(highs: List[float], lows: List[float], threshold: float = 0.02) -> bool:
        try:
            if not highs or not lows:
                return False

            high = max(highs)
            low = min(lows)

            if low == 0:
                return False

            return (high - low) / low < threshold

        except Exception as e:
            logger.error(f"Range detection error: {e}")
            return False

    # =========================
    # 🚀 BREAKOUT
    # =========================
    @staticmethod
    def breakout(close: float, highs: List[float]) -> bool:
        try:
            if not highs:
                return False

            resistance = max(highs[:-1])  # exclude current candle

            return close > resistance

        except Exception as e:
            logger.error(f"Breakout error: {e}")
            return False

    # =========================
    # 💥 BREAKDOWN
    # =========================
    @staticmethod
    def breakdown(close: float, lows: List[float]) -> bool:
        try:
            if not lows:
                return False

            support = min(lows[:-1])

            return close < support

        except Exception as e:
            logger.error(f"Breakdown error: {e}")
            return False

    # =========================
    # ⚠️ FAKE BREAKOUT
    # =========================
    @staticmethod
    def fake_breakout(candles: List[List[float]]) -> bool:
        try:
            if len(candles) < 3:
                return False

            prev = candles[-2]
            curr = candles[-1]

            prev_high = prev[2]
            curr_close = curr[4]

            # Break above then close below
            return curr[2] > prev_high and curr_close < prev_high

        except Exception as e:
            logger.error(f"Fake breakout error: {e}")
            return False

    # =========================
    # 🔥 STRONG BULLISH CANDLE
    # =========================
    @staticmethod
    def strong_bullish(candle: List[float]) -> bool:
        try:
            open_ = candle[1]
            high = candle[2]
            low = candle[3]
            close = candle[4]

            body = close - open_
            total = high - low

            if total == 0:
                return False

            return close > open_ and (body / total) > 0.6

        except Exception as e:
            logger.error(f"Bullish candle error: {e}")
            return False

    # =========================
    # 🔻 STRONG BEARISH CANDLE
    # =========================
    @staticmethod
    def strong_bearish(candle: List[float]) -> bool:
        try:
            open_ = candle[1]
            high = candle[2]
            low = candle[3]
            close = candle[4]

            body = open_ - close
            total = high - low

            if total == 0:
                return False

            return close < open_ and (body / total) > 0.6

        except Exception as e:
            logger.error(f"Bearish candle error: {e}")
            return False