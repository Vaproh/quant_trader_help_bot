from typing import Dict, List


class PullbackStrategy:

    def __init__(
        self,
        ema_period: int = 20,
        rr: float = 2.0,
        tolerance: float = 0.003
    ):
        self.ema_period = ema_period
        self.rr = rr
        self.tolerance = tolerance

    # =========================
    # 📊 EMA
    # =========================
    def _ema(self, prices: List[float], period: int) -> float:
        if len(prices) < period:
            return prices[-1]

        k = 2 / (period + 1)
        ema = prices[0]

        for price in prices[1:]:
            ema = price * k + ema * (1 - k)

        return ema

    # =========================
    # 📈 TREND STRENGTH
    # =========================
    def _trend_strength(self, closes: List[float], ema: float) -> float:
        recent = closes[-5:]

        above = sum(1 for c in recent if c > ema)
        below = sum(1 for c in recent if c < ema)

        return (above - below) / 5  # range [-1, 1]

    # =========================
    # 🔍 ANALYZE
    # =========================
    def analyze(self, mtf_candles) -> Dict:
        if isinstance(mtf_candles, dict):
            candles = mtf_candles.get("1m", [])
        else:
            candles = mtf_candles

        if len(candles) < self.ema_period + 5:
            return {"signal": None}

        closes = [c[4] for c in candles]

        ema = self._ema(closes, self.ema_period)

        last = candles[-1]
        prev = candles[-2]

        close = last[4]
        prev_close = prev[4]

        high = last[2]
        low = last[3]

        score = 0

        trend = self._trend_strength(closes, ema)

        # =========================
        # 🟢 LONG PULLBACK
        # =========================
        if close > ema:

            score += 40  # base

            # trend strength
            score += max(0, trend) * 20

            # pullback proximity
            distance = abs(close - ema) / ema
            if distance < self.tolerance:
                score += 15
            else:
                score -= 10

            # rejection confirmation
            if close > prev_close:
                score += 15
            else:
                score -= 10

            # wick confirmation
            candle_range = high - low
            if candle_range > 0:
                lower_wick = close - low
                if lower_wick / candle_range > 0.4:
                    score += 10

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
                "strategy": "pullback",
                "reason": "Bullish pullback to EMA"
            }

        # =========================
        # 🔴 SHORT PULLBACK
        # =========================
        if close < ema:

            score += 40

            score += max(0, -trend) * 20

            distance = abs(close - ema) / ema
            if distance < self.tolerance:
                score += 15
            else:
                score -= 10

            if close < prev_close:
                score += 15
            else:
                score -= 10

            candle_range = high - low
            if candle_range > 0:
                upper_wick = high - close
                if upper_wick / candle_range > 0.4:
                    score += 10

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
                "strategy": "pullback",
                "reason": "Bearish pullback to EMA"
            }

        return {"signal": None}