from typing import Dict, List
import ta
import pandas as pd
import numpy as np

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

from analysis.regime_detector import MarketRegimeDetector


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

    def __init__(self, strategy_names: List[str] = None, scanner=None, min_confidence=None):

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
        self.min_confidence = min_confidence or SETTINGS["strategy_decider"].get("min_confidence", SETTINGS["decision"]["min_confidence"])
        self.max_signals = SETTINGS["strategy_decider"]["max_signals_per_cycle"]

        self.regime_detector = MarketRegimeDetector()
        self.scanner = scanner

        logger.info(f"Loaded strategies: {strategy_names} (min_confidence={self.min_confidence})")

    # =========================
    # 🧠 MAIN DECISION FUNCTION
    # =========================
    def decide(
        self,
        mtf_candles: Dict[str, List[List[float]]],
        sentiment: Dict,
        symbol: str = None
    ) -> Dict:

        try:
            candles = mtf_candles.get("1m", [])
            if not candles or len(candles) < 50:
                return self._no_trade("Not enough 1m data")

            # Detect market regime
            regime_info = self.regime_detector.detect_regime(candles)
            regime = regime_info["regime"]
            regime_conf = regime_info["confidence"]

            signals = []

            # =========================
            # 📊 RUN STRATEGIES
            # =========================
            for strat in self.strategies:
                try:
                    result = strat.analyze(mtf_candles)

                    if result and result.get("signal"):
                        # Field validation
                        required_fields = ["strategy", "confidence", "reason"]
                        if not all(field in result for field in required_fields):
                            logger.warning(f"{strat.__class__.__name__} missing required fields: {required_fields}")
                            continue
                        signals.append(result)

                except Exception as e:
                    logger.warning(f"{strat.__class__.__name__} failed: {e}")

            logger.info(f"[{symbol or 'UNKNOWN'}] Raw signals: {len(signals)} | Regime: {regime} | Strategies: {[s['strategy'] for s in signals]}")
            for s in signals:
                logger.info(f"  → {s['strategy']}: {s['signal']} | conf: {s['confidence']:.1f} | {s['reason']}")

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
            # 📊 REGIME BIAS
            # =========================
            for s in signals:
                strategy = s.get("strategy", "")
                if regime == "TRENDING" and strategy in ["breakout", "momentum"]:
                    s["confidence"] += 10
                elif regime == "RANGING" and strategy == "range":
                    s["confidence"] += 10
                elif regime == "CHOPPY":
                    s["confidence"] -= 15  # Reduce confidence in choppy markets

                s["confidence"] = max(0, min(100, s["confidence"]))

            # =========================
            # 🎯 CONFLUENCE SCORING
            # =========================
            for s in signals:
                confluence_bonus = self._calculate_confluence(s, mtf_candles, sentiment, symbol)
                s["confidence"] += confluence_bonus
                s["confidence"] = max(0, min(100, s["confidence"]))

            # =========================
            # 🎯 FILTER
            # =========================
            signals_before = len(signals)
            signals = [
                s for s in signals
                if s["confidence"] >= self.min_confidence
            ]
            signals_after = len(signals)

            logger.info(f"Confidence filter (>= {self.min_confidence}): {signals_after}/{signals_before} pass")

            if not signals:
                return self._no_trade(f"All signals weak (Regime: {regime})")

            # =========================
            # 🏆 SORT
            # =========================
            signals.sort(key=lambda x: x["confidence"], reverse=True)

            # limit signals
            signals = signals[:self.max_signals]

            best = signals[0]

            logger.info(
                f"BEST → {best['strategy']} | {best['signal']} | {best['confidence']}% | {best['reason']}"
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

    # =========================
    # 🎯 CALCULATE CONFLUENCE
    # =========================
    def _calculate_confluence(self, signal: Dict, mtf_candles: Dict, sentiment: Dict, symbol: str = None) -> float:
        bonus = 0

        side = signal.get("signal")
        candles_1m = mtf_candles.get("1m", [])
        candles_15m = mtf_candles.get("15m", [])

        if len(candles_1m) < 20 or len(candles_15m) < 10:
            return 0

        # RSI alignment
        if len(candles_1m) >= 20:
            closes_1m = pd.Series([c[4] for c in candles_1m])
            rsi_indicator = ta.momentum.RSIIndicator(close=closes_1m, window=14)
            rsi_series = rsi_indicator.rsi()
            if len(rsi_series) > 0:
                rsi_current = rsi_series.iloc[-1]
                if (side == "LONG" and rsi_current > 50) or (side == "SHORT" and rsi_current < 50):
                    bonus += 5

        # Volume confirmation
        volumes = [c[5] for c in candles_1m[-10:]]
        if len(volumes) >= 5:
            avg_vol = sum(volumes) / len(volumes)
            last_vol = volumes[-1]
            if last_vol > avg_vol * 1.2:
                bonus += 5
            elif avg_vol < 100000:  # Low liquidity threshold (adjust)
                bonus -= 10  # Penalize low liquidity

        # Trend alignment (15m)
        if len(candles_15m) >= 10:
            highs_15 = [c[2] for c in candles_15m[-10:]]
            lows_15 = [c[3] for c in candles_15m[-10:]]
            resistance = max(highs_15)
            support = min(lows_15)

            entry = signal.get("entry", 0)
            tolerance = 0.005  # 0.5%

            if side == "LONG" and abs(entry - resistance) / entry < tolerance:
                bonus -= 15  # Near resistance, bad for long
            elif side == "SHORT" and abs(entry - support) / entry < tolerance:
                bonus -= 15  # Near support, bad for short

            # Trend
            closes_15 = [c[4] for c in candles_15m[-5:]]
            trend_up = closes_15[-1] > closes_15[0]
            if (side == "LONG" and trend_up) or (side == "SHORT" and not trend_up):
                bonus += 5

        # Volume confirmation
        volumes = [c[5] for c in candles_1m[-10:]]
        if len(volumes) >= 5:
            avg_vol = sum(volumes) / len(volumes)
            last_vol = volumes[-1]
            if last_vol > avg_vol * 1.2:
                bonus += 5
            elif avg_vol < 100000:  # Low liquidity threshold (adjust)
                bonus -= 10  # Penalize low liquidity

        # Trend alignment (15m)
        if len(candles_15m) >= 10:
            highs_15 = [c[2] for c in candles_15m[-10:]]
            lows_15 = [c[3] for c in candles_15m[-10:]]
            resistance = max(highs_15)
            support = min(lows_15)

            entry = signal.get("entry", 0)
            tolerance = 0.005  # 0.5%

            if side == "LONG" and abs(entry - resistance) / entry < tolerance:
                bonus -= 15  # Near resistance, bad for long
            elif side == "SHORT" and abs(entry - support) / entry < tolerance:
                bonus -= 15  # Near support, bad for short

            # Trend
            closes_15 = [c[4] for c in candles_15m[-5:]]
            trend_up = closes_15[-1] > closes_15[0]
            if (side == "LONG" and trend_up) or (side == "SHORT" and not trend_up):
                bonus += 5

        # Sentiment alignment
        sent_label = sentiment.get("sentiment", "NEUTRAL")
        if (side == "LONG" and sent_label == "BULLISH") or (side == "SHORT" and sent_label == "BEARISH"):
            bonus += 5

        # Hot list bonus
        if self.scanner and symbol and symbol in self.scanner.hot_list:
            bonus += 10

        return bonus