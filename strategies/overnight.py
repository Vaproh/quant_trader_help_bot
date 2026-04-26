from typing import Dict, List
from datetime import datetime
import pytz


class OvernightStrategy:

    def __init__(
        self,
        lookback: int = 10,
        rr: float = 1.5
    ):
        self.lookback = lookback
        self.rr = rr

        # Indian Standard Time
        self.ist = pytz.timezone("Asia/Kolkata")

    # =========================
    # 🕒 TIME FILTER (IST)
    # =========================
    def _is_overnight(self) -> bool:
        now = datetime.now(self.ist)
        hour = now.hour

        # 9 PM → 1 AM
        return hour >= 21 or hour <= 1

    # =========================
    # 📊 VOLATILITY CHECK
    # =========================
    def _volatility(self, candles: List[List]) -> float:
        ranges = [(c[2] - c[3]) for c in candles]
        avg_range = sum(ranges) / len(ranges)
        avg_price = sum(c[4] for c in candles) / len(candles)

        return avg_range / avg_price

    # =========================
    # 🔍 ANALYZE
    # =========================
    def analyze(self, mtf_candles) -> Dict:
        if isinstance(mtf_candles, dict):
            candles = mtf_candles.get("1m", [])
        else:
            candles = mtf_candles

        if len(candles) < self.lookback + 5:
            return {"signal": None}

        # =========================
        # ⛔ TIME FILTER
        # =========================
        if not self._is_overnight():
            return {"signal": None}

        recent = candles[-self.lookback:]

        closes = [c[4] for c in recent]

        last = candles[-1]
        prev = candles[-2]

        close = last[4]
        prev_close = prev[4]

        high = last[2]
        low = last[3]

        score = 0

        # =========================
        # 📊 VOLATILITY FILTER
        # =========================
        vol = self._volatility(recent)

        if vol > 0.01:  # too volatile
            return {"signal": None}

        score += 40  # base

        # =========================
        # 📈 DIRECTION
        # =========================
        move = close - closes[0]
        relative_move = move / closes[0]

        # =========================
        # 🟢 LONG
        # =========================
        if relative_move > 0:

            # smooth movement
            if abs(relative_move) < 0.01:
                score += 20
            else:
                score -= 10

            # continuation
            if close > prev_close:
                score += 10
            else:
                score -= 10

            # avoid choppy candles
            candle_range = high - low
            if candle_range > 0:
                body = abs(close - prev_close)
                if body / candle_range < 0.3:
                    score -= 15

            entry = close
            stop_loss = low
            risk = entry - stop_loss

            if risk <= 0:
                return {"signal": None}

            take_profit = entry + risk * self.rr

            confidence = max(0, min(100, score))

            if confidence < 50:
                return {"signal": None}

            return {
                "signal": "LONG",
                "entry": entry,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "confidence": confidence,
                "score": score,
                "strategy": "overnight",
                "reason": "Overnight bullish drift"
            }

        # =========================
        # 🔴 SHORT
        # =========================
        if relative_move < 0:

            if abs(relative_move) < 0.01:
                score += 20
            else:
                score -= 10

            if close < prev_close:
                score += 10
            else:
                score -= 10

            candle_range = high - low
            if candle_range > 0:
                body = abs(close - prev_close)
                if body / candle_range < 0.3:
                    score -= 15

            entry = close
            stop_loss = high
            risk = stop_loss - entry

            if risk <= 0:
                return {"signal": None}

            take_profit = entry - risk * self.rr

            confidence = max(0, min(100, score))

            if confidence < 50:
                return {"signal": None}

            return {
                "signal": "SHORT",
                "entry": entry,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "confidence": confidence,
                "score": score,
                "strategy": "overnight",
                "reason": "Overnight bearish drift"
            }

        return {"signal": None}