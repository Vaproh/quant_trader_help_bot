import time

from utils.logger import get_logger
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
        balance: float = 100.0,
        loop_delay: int = 10,
        repo=None,
        strategy_names=None
    ):
        self.market = market
        self.news = news

        self.symbol = symbol
        self.interval = interval
        self.loop_delay = loop_delay

        # Core
        self.decider = StrategyDecider(strategy_names=strategy_names)
        self.decision_engine = DecisionEngine()
        self.sizer = PositionSizer(balance=balance)
        self.manager = TradeManager()

        # External systems
        self.telegram = TelegramMainBot()
        self.stats_bot = TelegramStatsBot()
        self.repo = repo

        # Charts
        self.chart = ChartGenerator()

        # 🔥 CONTROL SYSTEM
        self.last_trade_time = 0
        self.trade_cooldown = 60  # seconds

        self.last_strategy = None
        self.last_entry_price = None

        self.running = False

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

        candles = self.market.get_klines(self.symbol, self.interval, 100)

        if not candles:
            logger.warning("No market data")
            return

        current_price = candles[-1][4]

        sentiment = self.news.get_sentiment(self.symbol.split("/")[0])

        raw = self.decider.decide(candles, sentiment)
        trade = self.decision_engine.build(raw)

        # =========================
        # 📥 OPEN TRADE (WITH FILTERS)
        # =========================
        if trade.get("action") == "TRADE":

            # ⏳ COOLDOWN
            if time.time() - self.last_trade_time < self.trade_cooldown:
                logger.info("Cooldown active, skipping trade")
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
                chart_path = self.chart.generate_trade_chart(
                    symbol=self.symbol,
                    candles=candles,
                    entry=trade["entry"],
                    stop_loss=trade["stop_loss"],
                    take_profit=trade["take_profit"]
                )

                logger.info(f"Trade opened: {trade}")

                # 📤 TELEGRAM
                self.telegram.send_trade(trade, self.symbol, chart_path)

                # 🔥 UPDATE CONTROL STATE
                self.last_trade_time = time.time()
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

        # =========================
        # 📊 SEND STATS
        # =========================
        if len(self.manager.closed_trades) >= 5:
            stats = Stats(self.manager.closed_trades).summary()
            self.stats_bot.send_stats(stats)

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
            self.stats_bot.send_trade_result(trade, self.symbol)

            trade["counted"] = True