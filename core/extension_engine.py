import threading
import time
from typing import List

from utils.logger import get_logger
from execution.paper_trader import PaperTrader
from bots.telegram_extension import TelegramExtensionBot
from core.strategy_decider import StrategyDecider
from core.decision import DecisionEngine
from config.constants import EXTENSION_MAX_LEVERAGE


logger = get_logger(__name__)


class ExtensionEngine:

    def __init__(
        self,
        market,
        news,
        symbols: List[str],
        balance: float = 100.0,
        loop_delay: int = 5,
        strategy_names = None
    ):
        self.market = market
        self.news = news
        self.symbols = symbols

        self.strategy_names = strategy_names

        self.loop_delay = loop_delay
        self.balance = balance

        self.telegram = TelegramExtensionBot()

        self.traders: List[PaperTrader] = []
        self.threads: List[threading.Thread] = []
        self.running = False

        self._init_traders()

    # =========================
    # ⚙️ INIT TRADERS
    # =========================
    def _init_traders(self):

        for symbol in self.symbols:

            trader = PaperTrader(
                market=self.market,
                news=self.news,
                symbol=symbol,
                interval="1m",
                balance=self.balance,
                loop_delay=self.loop_delay,
                strategy_names=self.strategy_names
            )

            # Override decision behavior
            trader.decision_engine = DecisionEngine()

            self.traders.append(trader)

    # =========================
    # 🚀 START ENGINE
    # =========================
    def start(self):

        logger.info("⚡ Extension Engine starting...")

        self.running = True

        for trader in self.traders:
            t = threading.Thread(
                target=self._run_trader,
                args=(trader,),
                daemon=True
            )
            self.threads.append(t)
            t.start()

        while self.running:
            time.sleep(self.loop_delay)

    # =========================
    # 🧵 RUN TRADER
    # =========================
    def _run_trader(self, trader: PaperTrader):

        while self.running:
            try:
                self._cycle(trader)
            except Exception as e:
                logger.error(f"Extension trader error: {e}")

            time.sleep(self.loop_delay)

    # =========================
    # 🔄 CYCLE
    # =========================
    def _cycle(self, trader: PaperTrader):

        candles = trader.market.get_klines(trader.symbol, trader.interval, 100)

        if not candles:
            return

        current_price = candles[-1][4]

        sentiment = trader.news.get_sentiment(trader.symbol.split("/")[0])

        raw = trader.decider.decide(candles, sentiment)

        trade = trader.decision_engine.build(raw)

        # =========================
        # ⚡ FORCE HIGH RISK LOGIC
        # =========================
        if trade.get("action") == "TRADE":

            # Increase leverage aggressively
            trade["leverage"] = min(
                trade.get("leverage", 1) + 2,
                EXTENSION_MAX_LEVERAGE
            )

            # Optional: slightly tighter SL (more aggressive)
            if trade["side"] == "LONG":
                trade["stop_loss"] *= 0.995
            else:
                trade["stop_loss"] *= 1.005

            size = trader.sizer.size(trade["entry"], trade["stop_loss"])
            trade["size"] = size

            opened = trader.manager.open_trade(trade)

            if opened:
                logger.info(f"⚡ Extension trade: {trade}")
                self.telegram.send_trade(trade, trader.symbol)

        # Update trades
        trader.manager.update_trades(current_price)

    # =========================
    # 🛑 STOP ENGINE
    # =========================
    def stop(self):

        logger.info("🛑 Stopping Extension Engine...")

        self.running = False

        for t in self.threads:
            t.join(timeout=2)

        logger.info("Extension Engine stopped")