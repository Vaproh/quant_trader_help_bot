from typing import Dict, List


class FakeBreakoutStrategy:

    def __init__(
        self,
        lookback: int = 20,
        rr: float = 2.0,
        tolerance: float = 0.002
    ):
        self.lookback = lookback
        self.rr = rr
        self.tolerance = tolerance

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
        # 🔴 FAKE BREAKOUT ABOVE (SHORT)
        # =========================
        if prev_close > resistance and close < resistance:

            score += 40  # base fake breakout

            # depth of fake breakout
            fake_depth = (prev_close - resistance) / resistance
            score += min(20, fake_depth * 2000)

            # rejection strength (upper wick)
            candle_range = high - low
            if candle_range > 0:
                upper_wick = high - close
                if upper_wick / candle_range > 0.4:
                    score += 20
                else:
                    score -= 10

            # reversal confirmation
            if close < prev_close:
                score += 15
            else:
                score -= 10

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
                "strategy": "fake_breakout",
                "reason": "Failed breakout above resistance"
            }

        # =========================
        # 🟢 FAKE BREAKDOWN BELOW (LONG)
        # =========================
        if prev_close < support and close > support:

            score += 40

            fake_depth = (support - prev_close) / support
            score += min(20, fake_depth * 2000)

            candle_range = high - low
            if candle_range > 0:
                lower_wick = close - low
                if lower_wick / candle_range > 0.4:
                    score += 20
                else:
                    score -= 10

            if close > prev_close:
                score += 15
            else:
                score -= 10

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
                "strategy": "fake_breakout",
                "reason": "Failed breakdown below support"
            }

        return {"signal": None}