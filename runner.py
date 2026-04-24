import threading
import time

from utils.logger import setup_logger, get_logger

from storage.repository import Repository
from storage.cache import Cache

from data.market_data import MarketData
from data.news import NewsAnalyzer

from core.engine import TradingEngine
from core.extension_engine import ExtensionEngine
from core.watchlist_engine import WatchlistEngine

from config.constants import DEFAULT_SYMBOLS
from config.secrets import SECRETS


logger = get_logger(__name__)


class Runner:

    def __init__(self):

        # =========================
        # ⚙️ SETUP LOGGER
        # =========================
        setup_logger()
        logger.info("Initializing Runner...")

        # =========================
        # 🗄 DATABASE
        # =========================
        self.repo = Repository()

        # =========================
        # ⚡ CACHE
        # =========================
        self.cache = Cache()

        # =========================
        # 📊 DATA LAYER
        # =========================
        self.market = MarketData(cache=self.cache)

        self.news = NewsAnalyzer(
            news_api_key=SECRETS["news_api_key"],
            ai_api_key=SECRETS["ai_api_key"],
            cache=self.cache
        )

        # =========================
        # 🧠 ENGINES
        # =========================
        self.main_engine = self._init_main_engine()
        self.extension_engine = self._init_extension_engine()
        self.watchlist_engine = self._init_watchlist_engine()

        self.threads = []

    # =========================
    # 🧠 MAIN ENGINE (SAFE)
    # =========================
    def _init_main_engine(self):

        from execution.paper_trader import PaperTrader

        traders = []

        main_strategies = [
            "breakout",
            "pullback",
            "range",
            "momentum"
        ]

        for symbol in DEFAULT_SYMBOLS:
            trader = PaperTrader(
                market=self.market,
                news=self.news,
                symbol=symbol,
                repo=self.repo,
                strategy_names=main_strategies
            )
            traders.append(trader)

        return TradingEngine(traders)

    # =========================
    # ⚡ EXTENSION ENGINE (AGGRESSIVE)
    # =========================
    def _init_extension_engine(self):

        extension_strategies = [
            "breakout",
            "momentum",
            "volume_spike",
            "fake_breakout",
            "pump"
        ]

        return ExtensionEngine(
            market=self.market,
            news=self.news,
            symbols=DEFAULT_SYMBOLS,
            balance=100,
            loop_delay=5,
            strategy_names=extension_strategies
        )

    # =========================
    # 👀 WATCHLIST ENGINE (SMART)
    # =========================
    def _init_watchlist_engine(self):

        watchlist_strategies = [
            "breakout",
            "pullback",
            "fake_breakout",
            "volume_spike",
            "overnight"
        ]

        return WatchlistEngine(
            market=self.market,
            news=self.news,
            symbols=[],  # 🔥 safe default (no crash)
            balance=100,
            loop_delay=15,
            strategy_names=watchlist_strategies
        )

    # =========================
    # 🚀 START SYSTEM
    # =========================
    def start(self):

        logger.info("🚀 Starting FULL SYSTEM...")

        self._start_thread(self.main_engine.start)
        self._start_thread(self.extension_engine.start)
        self._start_thread(self.watchlist_engine.start)

        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            self.stop()

    # =========================
    # 🧵 THREAD HELPER
    # =========================
    def _start_thread(self, target):

        t = threading.Thread(target=target, daemon=True)
        self.threads.append(t)
        t.start()

    # =========================
    # 🛑 STOP SYSTEM
    # =========================
    def stop(self):

        logger.info("🛑 Stopping system...")

        try:
            self.main_engine.stop()
        except:
            pass

        try:
            self.extension_engine.stop()
        except:
            pass

        try:
            self.watchlist_engine.stop()
        except:
            pass

        logger.info("System stopped")