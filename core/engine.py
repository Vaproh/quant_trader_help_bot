import threading
import time
from typing import List

from utils.logger import get_logger
from execution.paper_trader import PaperTrader
from analysis.market_scanner import MarketScanner
from config.settings import SETTINGS


logger = get_logger(__name__)


class TradingEngine:

    def __init__(
        self,
        traders: List[PaperTrader],
        cycle_delay: int = None,
        scanner=None
    ):
        self.traders = traders
        self.cycle_delay = cycle_delay or SETTINGS["engine"]["cycle_delay"]
        self.scanner = scanner

        # Assign scanner to traders
        for trader in self.traders:
            trader.scanner = self.scanner
        self.threads: List[threading.Thread] = []
        self.running = False

    # =========================
    # 🚀 START ENGINE
    # =========================
    def start(self):
        logger.info("🚀 Engine starting...")

        self.running = True

        for trader in self.traders:
            t = threading.Thread(
                target=self._run_trader,
                args=(trader,),
                daemon=True
            )
            self.threads.append(t)
            t.start()

        # Keep main thread alive
        while self.running:
            time.sleep(self.cycle_delay)

    # =========================
    # 🧵 RUN SINGLE TRADER
    # =========================
    def _run_trader(self, trader: PaperTrader):
        while self.running:
            try:
                trader.start()
            except Exception as e:
                logger.error(f"Trader {trader.symbol} crashed: {e}, restarting in 5 seconds")
                trader.running = False  # Ensure stopped
                time.sleep(5)
            else:
                # Normal exit when stopped
                break

    # =========================
    # 🛑 STOP ENGINE
    # =========================
    def stop(self):
        logger.info("🛑 Stopping engine...")

        self.running = False

        for trader in self.traders:
            trader.stop()

        for t in self.threads:
            t.join(timeout=2)

        logger.info("Engine stopped")