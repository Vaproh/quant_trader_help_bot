from typing import Dict, List


class MomentumStrategy:

    def __init__(
        self,
        lookback: int = 10,
        rr: float = 1.8,
        extension_limit: float = 0.01  # 1% max extension
    ):
        self.lookback = lookback
        self.rr = rr
        self.extension_limit = extension_limit

    # =========================
    # 📈 TREND CONSISTENCY
    # =========================
    def _trend_score(self, closes: List[float]) -> float:
        moves = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

        positive = sum(1 for m in moves if m > 0)
        negative = sum(1 for m in moves if m < 0)

        total = len(moves)

        if total == 0:
            return 0

        return (positive - negative) / total  # range [-1, 1]

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

        closes = [c[4] for c in candles[-self.lookback:]]

        last = candles[-1]
        prev = candles[-2]

        close = last[4]
        prev_close = prev[4]

        high = last[2]
        low = last[3]

        score = 0

        trend = self._trend_score(closes)

        price_change = close - closes[0]
        relative_move = price_change / closes[0]

        # =========================
        # 🟢 LONG MOMENTUM
        # =========================
        if trend > 0.4:

            score += 40  # base

            # trend consistency
            score += trend * 20

            # strong move
            if relative_move > 0.003:  # 0.3% move
                score += 20
            else:
                score -= 10

            # continuation candle
            if close > prev_close:
                score += 10
            else:
                score -= 10

            # overextension penalty
            extension = (close - closes[-3]) / closes[-3]
            if extension > self.extension_limit:
                score -= 20

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
                "strategy": "momentum",
                "reason": "Strong bullish momentum"
            }

        # =========================
        # 🔴 SHORT MOMENTUM
        # =========================
        if trend < -0.4:

            score += 40

            score += abs(trend) * 20

            if relative_move < -0.003:
                score += 20
            else:
                score -= 10

            if close < prev_close:
                score += 10
            else:
                score -= 10

            extension = (closes[-3] - close) / closes[-3]
            if extension > self.extension_limit:
                score -= 20

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
                "strategy": "momentum",
                "reason": "Strong bearish momentum"
            }

        return {"signal": None}