from utils.logger import get_logger
from config.constants import DEFAULT_RISK_PER_TRADE


logger = get_logger(__name__)


class PositionSizer:

    def __init__(self, balance: float = 100.0):
        self.balance = balance

    # =========================
    # 💰 CALCULATE POSITION SIZE
    # =========================
    def size(self, entry: float, stop_loss: float) -> float:
        try:
            risk_amount = self.balance * DEFAULT_RISK_PER_TRADE

            risk_per_unit = abs(entry - stop_loss)

            if risk_per_unit == 0:
                return 0.0

            position_size = risk_amount / risk_per_unit

            return position_size

        except Exception as e:
            logger.error(f"Position sizing error: {e}")
            return 0.0

    # =========================
    # 📉 UPDATE BALANCE
    # =========================
    def update_balance(self, pnl: float):
        try:
            self.balance += pnl
            logger.info(f"Updated balance: {self.balance}")
        except Exception as e:
            logger.error(f"Balance update error: {e}")