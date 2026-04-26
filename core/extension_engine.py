import threading
import time
from typing import List

from utils.logger import get_logger
from execution.paper_trader import PaperTrader
from bots.telegram_extension import TelegramExtensionBot
from core.strategy_decider import StrategyDecider
from core.decision import DecisionEngine
from config.constants import EXTENSION_MAX_LEVERAGE
from config.settings import SETTINGS
from storage.repository import Repository


logger = get_logger(__name__)


class ExtensionEngine:

    def __init__(
        self,
        market,
        news,
        symbols: List[str],
        balance: float = 100.0,
        loop_delay: int = 5,
        strategy_names = None,
        scanner=None,
        stats_bot=None,
        repo=None
    ):
        self.market = market
        self.news = news
        self.symbols = symbols

        self.strategy_names = strategy_names
        self.loop_delay = loop_delay
        self.balance = balance

        self.telegram = TelegramExtensionBot()
        self.scanner = scanner
        self.stats_bot = stats_bot
        self.repo = repo

        self.traders: List[PaperTrader] = []
        self.threads: List[threading.Thread] = []
        self.running = False

        # Extension-specific decision config
        self.min_confidence = SETTINGS["extension"]["min_confidence"]
        self.max_leverage = SETTINGS["extension"]["max_leverage"]

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
                strategy_names=self.strategy_names,
                scanner=self.scanner,
                stats_bot=self.stats_bot,
                repo=self.repo
            )

            # Override with EXTENSION-specific DecisionEngine
            trader.decision_engine = DecisionEngine(
                min_confidence=self.min_confidence,
                max_leverage=self.max_leverage
            )
            # Extension uses lower confidence threshold for strategy pre-filter
            trader.decider = StrategyDecider(
                strategy_names=self.strategy_names,
                scanner=self.scanner,
                min_confidence=self.min_confidence
            )

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

        logger.info(f"---- {trader.symbol} EXTENSION CYCLE ----")

        # Fetch MTF candles
        candles_1m = trader.market.get_klines(trader.symbol, "1m", 100)
        candles_15m = trader.market.get_klines(trader.symbol, "15m", 50)
        candles_1h = trader.market.get_klines(trader.symbol, "1h", 20)

        mtf_candles = {
            "1m": candles_1m,
            "15m": candles_15m,
            "1h": candles_1h
        }

        if not candles_1m:
            logger.warning("No 1m market data")
            return

        current_price = candles_1m[-1][4]

        sentiment = trader.news.get_sentiment(trader.symbol.split("/")[0])

        raw = trader.decider.decide(mtf_candles, sentiment, trader.symbol)
        logger.info(f"[EXTENSION RAW] {trader.symbol}: {raw}")

        trade = trader.decision_engine.build(raw)
        logger.info(f"[EXTENSION TRADE] {trader.symbol}: {trade}")

        # =========================
        # 📥 OPEN TRADE (WITH FILTERS)
        # =========================
        if trade.get("action") == "TRADE":

            now = time.time()
            side = trade.get("side")

            # ⏳ SYMBOL COOLDOWN
            last_symbol_trade = trader.symbol_cooldowns.get(trader.symbol, 0)
            if now - last_symbol_trade < trader.symbol_cooldown:
                logger.info(f"Symbol cooldown active for {trader.symbol}, skipping")
            else:
                # ⏳ DIRECTION COOLDOWN
                direction_key = f"{trader.symbol}_{side}"
                last_direction_trade = trader.direction_cooldowns.get(direction_key, 0)
                if now - last_direction_trade < trader.direction_cooldown:
                    logger.info(f"Direction cooldown active for {direction_key}, skipping")
                else:
                    # 🚫 SAME STRATEGY
                    if trade.get("strategy") == trader.last_strategy:
                        logger.info("Same strategy repeated, skipping")
                    else:
                        # 🚫 PRICE TOO CLOSE
                        if trader.last_entry_price:
                            change = abs(trade["entry"] - trader.last_entry_price) / trade["entry"]
                            if change < 0.001:
                                logger.info("Price too similar, skipping")
                            else:
                                # ⚡ APPLY AGGRESSIVE MODS
                                trade["leverage"] = min(
                                    trade.get("leverage", 1) + 2,
                                    EXTENSION_MAX_LEVERAGE
                                )

                                if trade["side"] == "LONG":
                                    trade["stop_loss"] *= 0.995
                                else:
                                    trade["stop_loss"] *= 1.005

                                # 📏 SIZE
                                trade["size"] = trader.sizer.size(
                                    trade["entry"], trade["stop_loss"]
                                )

                                opened = trader.manager.open_trade(trade)

                                if opened:
                                    # 🗄 SAVE TO DB
                                    if trader.repo:
                                        trade_id = trader.repo.insert_trade(trade, trader.symbol)
                                        trade["db_id"] = trade_id

                                    # 📊 GENERATE CHART
                                    try:
                                        chart_path = trader.chart.generate_trade_chart(
                                            symbol=trader.symbol,
                                            candles=candles_1m,
                                            entry=trade["entry"],
                                            stop_loss=trade["stop_loss"],
                                            take_profit=trade["take_profit"]
                                        )
                                    except Exception as e:
                                        logger.error(f"Chart generation error: {e}")
                                        chart_path = None

                                    logger.info(f"⚡ Extension trade opened: {trade}")

                                    # 📤 TELEGRAM (use extension bot)
                                    self.telegram.send_trade(trade, trader.symbol, chart_path)

                                    # 🔥 UPDATE CONTROL STATE
                                    now = time.time()
                                    trader.symbol_cooldowns[trader.symbol] = now
                                    trader.direction_cooldowns[f"{trader.symbol}_{side}"] = now
                                    trader.last_strategy = trade.get("strategy")
                                    trader.last_entry_price = trade["entry"]
        else:
            logger.info(f"Extension no trade: {trade.get('reason', 'unknown')}")

        # =========================
        # 📊 UPDATE TRADES (always)
        # =========================
        trader.manager.update_trades(current_price)

        # =========================
        # 💰 HANDLE CLOSED TRADES (always)
        # =========================
        trader._handle_closed_trades()

    # =========================
    # 🛑 STOP ENGINE
    # =========================
    def stop(self):

        logger.info("🛑 Stopping Extension Engine...")

        self.running = False

        for t in self.threads:
            t.join(timeout=2)

        logger.info("Extension Engine stopped")