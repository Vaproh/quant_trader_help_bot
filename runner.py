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
from analysis.market_scanner import MarketScanner
from core.strategy_decider import StrategyDecider
from core.decision import DecisionEngine

from bots.telegram_stats import TelegramStatsBot

from config.constants import DEFAULT_SYMBOLS
from config.secrets import SECRETS
from config.settings import SETTINGS


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
        # 🤖 SHARED TELEGRAM BOT
        # =========================
        self.stats_bot = TelegramStatsBot(repo=self.repo)

        # =========================
        # 🔍 MARKET SCANNER
        # =========================
        self.scanner = MarketScanner(self.market)

        # =========================
        # 🧠 ENGINES
        # =========================
        self.main_engine = self._init_main_engine(scanner=self.scanner)
        self.extension_engine = self._init_extension_engine(scanner=self.scanner)
        self.watchlist_engine = self._init_watchlist_engine(scanner=self.scanner)

        self.threads = []

    # =========================
    # 🧠 MAIN ENGINE (SAFE)
    # =========================
    def _init_main_engine(self, scanner=None):

        from execution.paper_trader import PaperTrader

        traders = []
        main_strategies = SETTINGS["engines"]["main"]

        for symbol in DEFAULT_SYMBOLS:
            trader = PaperTrader(
                market=self.market,
                news=self.news,
                symbol=symbol,
                repo=self.repo,
                strategy_names=main_strategies,
                scanner=scanner,
                stats_bot=self.stats_bot
            )
            # Main bot: high confidence threshold (70%+)
            trader.decision_engine = DecisionEngine(
                min_confidence=SETTINGS["decision"]["min_confidence"],
                max_leverage=SETTINGS["decision"]["max_leverage"]
            )
            # Main bot also uses high confidence for strategy pre-filter
            trader.decider = StrategyDecider(
                strategy_names=main_strategies,
                scanner=scanner,
                min_confidence=SETTINGS["decision"]["min_confidence"]
            )
            traders.append(trader)

        return TradingEngine(traders, scanner=scanner)

    # =========================
    # ⚡ EXTENSION ENGINE (AGGRESSIVE)
    # =========================
    def _init_extension_engine(self, scanner=None):

        extension_strategies = SETTINGS["engines"]["extension"]

        return ExtensionEngine(
            market=self.market,
            news=self.news,
            symbols=DEFAULT_SYMBOLS,
            balance=100,
            loop_delay=SETTINGS["extension"]["loop_delay"],
            strategy_names=extension_strategies,
            scanner=scanner,
            stats_bot=self.stats_bot,
            repo=self.repo
        )

    # =========================
    # 👀 WATCHLIST ENGINE (SMART)
    # =========================
    def _init_watchlist_engine(self, scanner=None):

        watchlist_strategies = SETTINGS["engines"]["watchlist"]

        return WatchlistEngine(
            market=self.market,
            news=self.news,
            symbols=[],  # 🔥 safe default (no crash)
            balance=100,
            loop_delay=SETTINGS["watchlist"]["loop_delay"],
            strategy_names=watchlist_strategies,
            repo=self.repo,
            scanner=scanner,
            stats_bot=self.stats_bot
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