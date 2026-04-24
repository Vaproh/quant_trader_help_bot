from typing import Dict, List

from utils.logger import get_logger

# Settings
from config.settings import SETTINGS

# Strategies
from strategies.breakout import BreakoutStrategy
from strategies.pullback import PullbackStrategy
from strategies.range import RangeStrategy
from strategies.momentum import MomentumStrategy
from strategies.volume_spike import VolumeSpikeStrategy
from strategies.fake_breakout import FakeBreakoutStrategy
from strategies.pump import PumpStrategy
from strategies.overnight import OvernightStrategy


logger = get_logger(__name__)


# =========================
# 🧠 STRATEGY FACTORY
# =========================
STRATEGY_MAP = {
    "breakout": BreakoutStrategy,
    "pullback": PullbackStrategy,
    "range": RangeStrategy,
    "momentum": MomentumStrategy,
    "volume_spike": VolumeSpikeStrategy,
    "fake_breakout": FakeBreakoutStrategy,
    "pump": PumpStrategy,
    "overnight": OvernightStrategy,
}


class StrategyDecider:

    def __init__(self, strategy_names: List[str] = None):

        # =========================
        # 🧠 LOAD STRATEGIES
        # =========================
        if strategy_names is None:
            strategy_names = SETTINGS["strategies"]["enabled"]

        self.strategies = []

        for name in strategy_names:
            if name in STRATEGY_MAP:
                self.strategies.append(STRATEGY_MAP[name]())
            else:
                logger.warning(f"Unknown strategy: {name}")

        # =========================
        # ⚙️ CONFIG
        # =========================
        self.min_confidence = SETTINGS["decision"]["min_confidence"]
        self.max_signals = SETTINGS["strategy_decider"]["max_signals_per_cycle"]

        logger.info(f"Loaded strategies: {strategy_names}")

    # =========================
    # 🧠 MAIN DECISION FUNCTION
    # =========================
    def decide(
        self,
        candles: List[List[float]],
        sentiment: Dict
    ) -> Dict:

        try:
            if not candles or len(candles) < 50:
                return self._no_trade("Not enough data")

            signals = []

            # =========================
            # 📊 RUN STRATEGIES
            # =========================
            for strat in self.strategies:
                try:
                    result = strat.analyze(candles)

                    if result and result.get("signal"):
                        signals.append(result)

                except Exception as e:
                    logger.warning(f"{strat.__class__.__name__} failed: {e}")

            if not signals:
                return self._no_trade("No strategy signal")

            # =========================
            # 🧠 SENTIMENT BIAS
            # =========================
            sentiment_label = sentiment.get("sentiment", "NEUTRAL")
            sentiment_conf = sentiment.get("confidence", 50)

            if sentiment_conf > 60:
                for s in signals:

                    if sentiment_label == "BULLISH" and s["signal"] == "LONG":
                        s["confidence"] += 5

                    elif sentiment_label == "BEARISH" and s["signal"] == "SHORT":
                        s["confidence"] += 5

                    s["confidence"] = max(0, min(100, s["confidence"]))

            # =========================
            # 🎯 FILTER
            # =========================
            signals = [
                s for s in signals
                if s["confidence"] >= self.min_confidence
            ]

            if not signals:
                return self._no_trade("All signals weak")

            # =========================
            # 🏆 SORT
            # =========================
            signals.sort(key=lambda x: x["confidence"], reverse=True)

            # limit signals
            signals = signals[:self.max_signals]

            best = signals[0]

            logger.info(
                f"BEST → {best['strategy']} | {best['signal']} | {best['confidence']}"
            )

            return self._build_trade(best)

        except Exception as e:
            logger.error(f"Decision error: {e}")
            return self._no_trade("Error")

    # =========================
    # 🎯 BUILD TRADE
    # =========================
    def _build_trade(self, s: Dict) -> Dict:

        return {
            "action": "TRADE",
            "side": s["signal"],
            "entry": s["entry"],
            "stop_loss": s["stop_loss"],
            "take_profit": s["take_profit"],
            "confidence": s["confidence"],
            "strategy": s["strategy"],
            "reason": s["reason"]
        }

    # =========================
    # ❌ NO TRADE
    # =========================
    def _no_trade(self, reason: str) -> Dict:

        return {
            "action": "WAIT",
            "reason": reason,
            "confidence": 0
        }