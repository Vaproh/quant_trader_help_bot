from typing import Dict

from utils.logger import get_logger
from utils.helpers import calculate_rr, safe_round
from config.settings import SETTINGS
from config.constants import MAIN_BOT_MAX_LEVERAGE, EXTENSION_MAX_LEVERAGE


logger = get_logger(__name__)


class DecisionEngine:

    def __init__(self, min_confidence=None, max_leverage=None, risk_pct=None, reward_pct=None):
        """
        Configurable Decision Engine.
        Parameters can be overridden per-engine.
        """
        self.min_confidence = min_confidence or SETTINGS["decision"]["min_confidence"]
        self.max_leverage = max_leverage or SETTINGS["decision"]["max_leverage"]
        self.risk_pct = risk_pct or 0.01   # 1%
        self.reward_pct = reward_pct or 0.02  # 2%

    # =========================
    # 🎯 BUILD FINAL TRADE
    # =========================
    def build(self, decision: Dict) -> Dict:

        try:
            if decision.get("action") != "TRADE":
                return decision

            side = decision["side"]
            entry = float(decision["entry"])
            confidence = decision["confidence"]
            strategy = decision.get("strategy", "unknown")

            # =========================
            # 🎯 CONFIDENCE FILTER
            # =========================
            if confidence < self.min_confidence:
                return {
                    "action": "WAIT",
                    "reason": f"Confidence {confidence} below threshold {self.min_confidence}",
                    "confidence": confidence
                }

            # =========================
            # SL / TP CALCULATION
            # =========================
            sl, tp = self._calculate_levels(side, entry)

            rr = calculate_rr(entry, sl, tp)

            # =========================
            # LEVERAGE DECISION
            # =========================
            leverage = self._decide_leverage(confidence, rr)

            # =========================
            # SPOT vs FUTURES
            # =========================
            trade_type = self._decide_type(leverage)

            return {
                "action": "TRADE",
                "side": side,
                "type": trade_type,
                "entry": safe_round(entry),
                "stop_loss": safe_round(sl),
                "take_profit": safe_round(tp),
                "rr": safe_round(rr, 2),
                "leverage": leverage,
                "confidence": confidence,
                "strategy": strategy,
                "reason": decision.get("reason", "")
            }

        except Exception as e:
            logger.error(f"Decision build error: {e}")
            return {
                "action": "WAIT",
                "reason": "Decision engine failed",
                "confidence": 0
            }

    # =========================
    # 📉 SL / TP LOGIC
    # =========================
    def _calculate_levels(self, side: str, entry: float):

        try:
            risk_pct = 0.01   # 1%
            reward_pct = 0.02  # 2%

            if side == "LONG":
                sl = entry * (1 - risk_pct)
                tp = entry * (1 + reward_pct)

            elif side == "SHORT":
                sl = entry * (1 + risk_pct)
                tp = entry * (1 - reward_pct)

            else:
                return entry, entry

            return sl, tp

        except Exception as e:
            logger.error(f"SL/TP error: {e}")
            return entry, entry

    # =========================
    # ⚡ LEVERAGE LOGIC
    # =========================
    def _decide_leverage(self, confidence: int, rr: float) -> int:

        try:
            base = 1

            if confidence > 70:
                base += 2

            if confidence > 85:
                base += 1

            if rr > 2:
                base += 1

            # Cap at engine-specific max
            return min(base, self.max_leverage)

        except Exception as e:
            logger.error(f"Leverage error: {e}")
            return 1

    # =========================
    # 📊 SPOT vs FUTURES
    # =========================
    def _decide_type(self, leverage: int) -> str:
        return "FUTURES" if leverage > 1 else "SPOT"