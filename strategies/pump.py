from typing import Dict, List


class PumpStrategy:

    def __init__(
        self,
        lookback: int = 5,
        rr: float = 1.5,
        max_extension: float = 0.02  # 2% cap
    ):
        self.lookback = lookback
        self.rr = rr
        self.max_extension = max_extension

    # =========================
    # 🔍 ANALYZE
    # =========================
    def analyze(self, candles: List[List]) -> Dict:

        if len(candles) < self.lookback + 5:
            return {"signal": None}

        closes = [c[4] for c in candles[-self.lookback:]]
        volumes = [c[5] for c in candles[-self.lookback:]]

        last = candles[-1]
        prev = candles[-2]

        close = last[4]
        prev_close = prev[4]

        high = last[2]
        low = last[3]

        score = 0

        # =========================
        # 📊 PRICE EXPLOSION
        # =========================
        move = close - closes[0]
        relative_move = move / closes[0]

        avg_volume = sum(volumes[:-1]) / (len(volumes) - 1)
        current_volume = volumes[-1]

        # =========================
        # 🟢 BULLISH PUMP
        # =========================
        if relative_move > 0.005:  # 0.5%+ fast move

            score += 40

            # explosiveness
            score += min(25, relative_move * 2000)

            # volume confirmation
            if current_volume > avg_volume * 1.5:
                score += 20
            else:
                score -= 10

            # continuation
            if close > prev_close:
                score += 10
            else:
                score -= 10

            # overextension penalty (VERY IMPORTANT)
            extension = (close - closes[-2]) / closes[-2]
            if extension > self.max_extension:
                score -= 30

            # rejection wick penalty
            candle_range = high - low
            if candle_range > 0:
                upper_wick = high - close
                if upper_wick / candle_range > 0.5:
                    score -= 20

            entry = close
            stop_loss = low
            risk = entry - stop_loss

            if risk <= 0:
                return {"signal": None}

            take_profit = entry + risk * self.rr

            confidence = max(0, min(100, score))

            if confidence < 55:  # stricter than others
                return {"signal": None}

            return {
                "signal": "LONG",
                "entry": entry,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "confidence": confidence,
                "score": score,
                "strategy": "pump",
                "reason": "Bullish pump detected"
            }

        # =========================
        # 🔴 BEARISH DUMP
        # =========================
        if relative_move < -0.005:

            score += 40

            score += min(25, abs(relative_move) * 2000)

            if current_volume > avg_volume * 1.5:
                score += 20
            else:
                score -= 10

            if close < prev_close:
                score += 10
            else:
                score -= 10

            extension = (closes[-2] - close) / closes[-2]
            if extension > self.max_extension:
                score -= 30

            candle_range = high - low
            if candle_range > 0:
                lower_wick = close - low
                if lower_wick / candle_range > 0.5:
                    score -= 20

            entry = close
            stop_loss = high
            risk = stop_loss - entry

            if risk <= 0:
                return {"signal": None}

            take_profit = entry - risk * self.rr

            confidence = max(0, min(100, score))

            if confidence < 55:
                return {"signal": None}

            return {
                "signal": "SHORT",
                "entry": entry,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "confidence": confidence,
                "score": score,
                "strategy": "pump",
                "reason": "Bearish dump detected"
            }

        return {"signal": None}