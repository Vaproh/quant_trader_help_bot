from typing import Dict, List


class BreakoutStrategy:

    def __init__(self, lookback: int = 20, rr: float = 2.0):
        self.lookback = lookback
        self.rr = rr

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
        # 🟢 LONG BREAKOUT
        # =========================
        if prev_close < resistance and close > resistance:

            entry = close
            stop_loss = support
            risk = entry - stop_loss

            if risk <= 0:
                return {"signal": None}

            take_profit = entry + risk * self.rr

            # =========================
            # 🧠 SCORING
            # =========================

            score += 40  # base breakout

            # strength of breakout candle
            candle_size = close - prev_close
            if candle_size / close > 0.002:
                score += 15

            # distance above resistance
            if close > resistance * 1.001:
                score += 10
            else:
                score -= 10

            # wick rejection (good sign)
            if close > (high - (high - low) * 0.3):
                score += 10

            # clamp confidence
            confidence = max(0, min(100, score))

            return {
                "signal": "LONG",
                "entry": entry,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "confidence": confidence,
                "score": score,
                "strategy": "breakout",
                "reason": "Resistance breakout"
            }

        # =========================
        # 🔴 SHORT BREAKDOWN
        # =========================
        if prev_close > support and close < support:

            entry = close
            stop_loss = resistance
            risk = stop_loss - entry

            if risk <= 0:
                return {"signal": None}

            take_profit = entry - risk * self.rr

            score += 40

            candle_size = prev_close - close
            if candle_size / close > 0.002:
                score += 15

            if close < support * 0.999:
                score += 10
            else:
                score -= 10

            if close < (low + (high - low) * 0.3):
                score += 10

            confidence = max(0, min(100, score))

            return {
                "signal": "SHORT",
                "entry": entry,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "confidence": confidence,
                "score": score,
                "strategy": "breakout",
                "reason": "Support breakdown"
            }

        return {"signal": None}