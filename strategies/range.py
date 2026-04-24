from typing import Dict, List


class RangeStrategy:

    def __init__(
        self,
        lookback: int = 20,
        rr: float = 1.8,
        tolerance: float = 0.003
    ):
        self.lookback = lookback
        self.rr = rr
        self.tolerance = tolerance

    # =========================
    # 📊 RANGE DETECTION
    # =========================
    def _is_ranging(self, highs: List[float], lows: List[float]) -> bool:
        range_size = max(highs) - min(lows)
        avg_price = sum(highs + lows) / (2 * len(highs))

        # small range relative to price → sideways
        return (range_size / avg_price) < 0.02  # 2%

    # =========================
    # 🔍 ANALYZE
    # =========================
    def analyze(self, candles: List[List]) -> Dict:

        if len(candles) < self.lookback + 5:
            return {"signal": None}

        highs = [c[2] for c in candles[-self.lookback:]]
        lows = [c[3] for c in candles[-self.lookback:]]

        resistance = max(highs)
        support = min(lows)

        last = candles[-1]
        prev = candles[-2]

        close = last[4]
        prev_close = prev[4]

        high = last[2]
        low = last[3]

        score = 0

        # =========================
        # 📉 CHECK RANGE CONDITION
        # =========================
        if not self._is_ranging(highs, lows):
            return {"signal": None}

        score += 40  # base

        range_size = resistance - support

        if range_size <= 0:
            return {"signal": None}

        # =========================
        # 🟢 LONG AT SUPPORT
        # =========================
        distance_to_support = abs(close - support) / support

        if distance_to_support < self.tolerance:

            # edge proximity
            score += 20

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
            stop_loss = support * 0.998  # slightly below support
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
                "strategy": "range",
                "reason": "Support bounce in range"
            }

        # =========================
        # 🔴 SHORT AT RESISTANCE
        # =========================
        distance_to_resistance = abs(close - resistance) / resistance

        if distance_to_resistance < self.tolerance:

            score += 20

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
            stop_loss = resistance * 1.002
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
                "strategy": "range",
                "reason": "Resistance rejection in range"
            }

        # =========================
        # ❌ MIDDLE OF RANGE → IGNORE
        # =========================
        return {"signal": None}