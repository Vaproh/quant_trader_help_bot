from typing import Dict, List


class VolumeSpikeStrategy:

    def __init__(
        self,
        lookback: int = 20,
        rr: float = 1.8,
        spike_threshold: float = 2.0
    ):
        self.lookback = lookback
        self.rr = rr
        self.spike_threshold = spike_threshold

    # =========================
    # 🔍 ANALYZE
    # =========================
    def analyze(self, candles: List[List]) -> Dict:

        if len(candles) < self.lookback + 5:
            return {"signal": None}

        volumes = [c[5] for c in candles[-self.lookback:]]
        closes = [c[4] for c in candles[-self.lookback:]]

        avg_volume = sum(volumes[:-1]) / (len(volumes) - 1)
        current_volume = volumes[-1]

        last = candles[-1]
        prev = candles[-2]

        close = last[4]
        prev_close = prev[4]

        high = last[2]
        low = last[3]

        score = 0

        # =========================
        # 📊 VOLUME SPIKE DETECTION
        # =========================
        if current_volume < avg_volume * self.spike_threshold:
            return {"signal": None}

        score += 40  # base

        spike_strength = current_volume / avg_volume
        score += min(25, (spike_strength - 1) * 10)

        # =========================
        # 🟢 BULLISH SPIKE
        # =========================
        if close > prev_close:

            # price reaction strength
            move = close - prev_close
            if move / close > 0.002:
                score += 20
            else:
                score -= 10

            # continuation
            if close > closes[-3]:
                score += 10

            # fake spike penalty (big wick)
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

            if confidence < 50:
                return {"signal": None}

            return {
                "signal": "LONG",
                "entry": entry,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "confidence": confidence,
                "score": score,
                "strategy": "volume_spike",
                "reason": "Bullish volume spike"
            }

        # =========================
        # 🔴 BEARISH SPIKE
        # =========================
        if close < prev_close:

            move = prev_close - close
            if move / close > 0.002:
                score += 20
            else:
                score -= 10

            if close < closes[-3]:
                score += 10

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

            if confidence < 50:
                return {"signal": None}

            return {
                "signal": "SHORT",
                "entry": entry,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "confidence": confidence,
                "score": score,
                "strategy": "volume_spike",
                "reason": "Bearish volume spike"
            }

        return {"signal": None}