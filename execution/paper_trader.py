import time

from utils.logger import get_logger
from config.settings import SETTINGS
from data.market_data import MarketData
from data.news import NewsAnalyzer
from core.strategy_decider import StrategyDecider
from core.decision import DecisionEngine
from execution.position_sizer import PositionSizer
from execution.trade_manager import TradeManager

from bots.telegram_main import TelegramMainBot
from bots.telegram_stats import TelegramStatsBot
from analysis.stats import Stats

from charts.chart_generator import ChartGenerator


logger = get_logger(__name__)


class PaperTrader:

    def __init__(
        self,
        market: MarketData,
        news: NewsAnalyzer,
        symbol: str = "BTC/USDT",
        interval: str = "1m",
        balance: float = None,
        loop_delay: int = None,
        repo=None,
        strategy_names=None,
        scanner=None,
        stats_bot=None
    ):
        self.market = market
        self.news = news

        self.symbol = symbol
        self.interval = interval
        self.loop_delay = loop_delay or SETTINGS["paper_trader"]["loop_delay"]
        self.balance = balance or SETTINGS["paper_trader"]["initial_balance"]

        # Core
        self.decider = StrategyDecider(strategy_names=strategy_names, scanner=scanner)
        self.decision_engine = DecisionEngine()
        self.sizer = PositionSizer(balance=self.balance)
        self.manager = TradeManager(max_trades=SETTINGS["paper_trader"]["max_open_trades"])

        # Charts
        self.chart = ChartGenerator()

        # 🔥 CONTROL SYSTEM
        self.symbol_cooldowns = {}  # symbol -> last_trade_time
        self.direction_cooldowns = {}  # symbol_side -> last_trade_time
        self.symbol_cooldown = SETTINGS["paper_trader"]["symbol_cooldown"]
        self.direction_cooldown = SETTINGS["paper_trader"]["direction_cooldown"]

        self.last_strategy = None
        self.last_entry_price = None

        # External systems (after manager/sizer)
        self.telegram = TelegramMainBot()
        self.stats_bot = stats_bot or TelegramStatsBot(repo=repo)
        self.repo = repo

        self.running = False

    # =========================
    # 📥 LOAD STATE
    # =========================
    def _load_state(self):
        if self.repo:
            # Load balance
            last_balance = self.repo.get_last_balance()
            if last_balance is not None:
                self.sizer.balance = last_balance
                logger.info(f"Loaded balance: {last_balance}")

            # Load active trades
            active_trades = self.repo.get_active_trades(self.symbol)
            self.manager.load_active_trades(active_trades)
            logger.info(f"Loaded {len(active_trades)} active trades for {self.symbol}")

    # =========================
    # 🚀 START LOOP
    # =========================
    def start(self):

        logger.info(f"📡 Paper Trader started: {self.symbol}")
        self.running = True

        while self.running:
            try:
                self._cycle()
            except Exception as e:
                logger.error(f"Cycle error: {e}")

            time.sleep(self.loop_delay)

    # =========================
    # 🛑 STOP LOOP
    # =========================
    def stop(self):
        self.running = False
        logger.info(f"🛑 Paper Trader stopped: {self.symbol}")

    # =========================
    # 🔄 SINGLE CYCLE
    # =========================
    def _cycle(self):

        logger.info(f"---- {self.symbol} NEW CYCLE ----")

        # Fetch multi-timeframe data
        candles_1m = self.market.get_klines(self.symbol, "1m", 100)
        candles_15m = self.market.get_klines(self.symbol, "15m", 50)
        candles_1h = self.market.get_klines(self.symbol, "1h", 20)

        mtf_candles = {
            "1m": candles_1m,
            "15m": candles_15m,
            "1h": candles_1h
        }

        if not candles_1m:
            logger.warning("No 1m market data")
            return

        current_price = candles_1m[-1][4]

        sentiment = self.news.get_sentiment(self.symbol.split("/")[0])

        raw = self.decider.decide(mtf_candles, sentiment, self.symbol)
        trade = self.decision_engine.build(raw)

        # =========================
        # 📥 OPEN TRADE (WITH FILTERS)
        # =========================
        if trade.get("action") == "TRADE":

            now = time.time()
            side = trade.get("side")

            # ⏳ SYMBOL COOLDOWN
            last_symbol_trade = self.symbol_cooldowns.get(self.symbol, 0)
            if now - last_symbol_trade < self.symbol_cooldown:
                logger.info(f"Symbol cooldown active for {self.symbol}, skipping")
                return

            # ⏳ DIRECTION COOLDOWN
            direction_key = f"{self.symbol}_{side}"
            last_direction_trade = self.direction_cooldowns.get(direction_key, 0)
            if now - last_direction_trade < self.direction_cooldown:
                logger.info(f"Direction cooldown active for {direction_key}, skipping")
                return

            # 🚫 SAME STRATEGY
            if trade.get("strategy") == self.last_strategy:
                logger.info("Same strategy repeated, skipping")
                return

            # 🚫 PRICE TOO CLOSE
            if self.last_entry_price:
                change = abs(trade["entry"] - self.last_entry_price) / trade["entry"]
                if change < 0.001:  # 0.1%
                    logger.info("Price too similar, skipping")
                    return

            # 📏 SIZE
            trade["size"] = self.sizer.size(
                trade["entry"], trade["stop_loss"]
            )

            opened = self.manager.open_trade(trade)

            if opened:

                # 🗄 SAVE TO DB
                if self.repo:
                    trade_id = self.repo.insert_trade(trade, self.symbol)
                    trade["db_id"] = trade_id

                # 📊 GENERATE CHART
                try:
                    chart_path = self.chart.generate_trade_chart(
                        symbol=self.symbol,
                        candles=candles_1m,
                        entry=trade["entry"],
                        stop_loss=trade["stop_loss"],
                        take_profit=trade["take_profit"]
                    )
                except Exception as e:
                    logger.error(f"Chart generation error: {e}")
                    chart_path = None

                logger.info(f"Trade opened: {trade}")

                # 📤 TELEGRAM
                self.telegram.send_trade(trade, self.symbol, chart_path)

                # 🔥 UPDATE CONTROL STATE
                now = time.time()
                self.symbol_cooldowns[self.symbol] = now
                self.direction_cooldowns[f"{self.symbol}_{side}"] = now
                self.last_strategy = trade.get("strategy")
                self.last_entry_price = trade["entry"]

        # =========================
        # 📊 UPDATE TRADES
        # =========================
        self.manager.update_trades(current_price)

        # =========================
        # 💰 HANDLE CLOSED TRADES
        # =========================
        self._handle_closed_trades()

        # =========================
        # 📈 STATUS
        # =========================
        logger.info(f"Balance: {self.sizer.balance:.2f}")
        logger.info(f"Active: {len(self.manager.active_trades)}")
        logger.info(f"Closed: {len(self.manager.closed_trades)}")

        # Stats are sent automatically when trades close via _handle_closed_trades
        # Use /stats command for on-demand summary

    # =========================
    # 💰 HANDLE CLOSED TRADES
    # =========================
    def _handle_closed_trades(self):

        for trade in self.manager.closed_trades:

            if trade.get("counted"):
                continue

            pnl = trade.get("pnl", 0)

            # 💰 UPDATE BALANCE
            self.sizer.update_balance(pnl)

            # 🗄 DB UPDATE
            if self.repo and trade.get("db_id"):
                self.repo.close_trade(
                    trade["db_id"],
                    pnl,
                    trade.get("result", "")
                )

                self.repo.save_balance(self.sizer.balance)

            # 📤 TELEGRAM RESULT
            if self.stats_bot:
                self.stats_bot.send_trade_result(trade, self.symbol)

            trade["counted"] = True