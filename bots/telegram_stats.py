import requests
import time
import threading
from typing import Dict, List

from utils.logger import get_logger
from config.secrets import SECRETS
from config.settings import SETTINGS
from utils.helpers import format_price, safe_round, safe_get
from analysis.stats import Stats
from storage.repository import Repository


logger = get_logger(__name__)


STRATEGY_EMOJI = {
    "breakout": "🚀",
    "pullback": "📉",
    "range": "📦",
    "momentum": "⚡",
    "volume_spike": "📊",
    "fake_breakout": "🪤",
    "pump": "🔥",
    "overnight": "🌙"
}


class TelegramStatsBot:

    def __init__(self, repo: Repository = None):
        self.token = SECRETS["telegram_stats_token"]
        self.chat_id = int(SECRETS["telegram_stats_chat_id"])
        self.base_url = f"https://api.telegram.org/bot{self.token}"

        self.repo = repo or Repository()

        self.last_update_id = 0
        self.polling_thread = threading.Thread(target=self._poll_updates, daemon=True)
        self.polling_thread.start()

        # Periodic stats (hourly)
        self.stats_interval = 3600  # 1 hour
        self.stats_thread = threading.Thread(target=self._periodic_stats, daemon=True)
        self.stats_thread.start()

    # =========================
    # 📤 SAFE SEND
    # =========================
    def send_message(self, text: str):

        url = f"{self.base_url}/sendMessage"

        for attempt in range(3):
            try:
                res = requests.post(
                    url,
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": "Markdown"
                    },
                    timeout=10
                )

                if res.status_code == 200:
                    logger.info("Stats message sent")
                    return True
                else:
                    logger.warning(f"Stats failed [{res.status_code}]: {res.text}")

            except Exception as e:
                logger.error(f"Stats send error (attempt {attempt+1}): {e}")

        logger.error("Stats message FAILED after retries")
        return False

    # =========================
    # 📊 FORMAT STATS
    # =========================
    def format_stats(self, stats: Dict) -> str:

        return f"""
📊 *BOT PERFORMANCE*

📈 Trades: `{safe_get(stats, 'total_trades', 0)}`
✅ Win Rate: `{safe_get(stats, 'win_rate', 0)}%`

💰 PnL: `{safe_round(safe_get(stats, 'total_pnl', 0), 2)}`
⚖️ Profit Factor: `{safe_get(stats, 'profit_factor', 0)}`

📊 Avg Win: `{safe_round(safe_get(stats, 'avg_win', 0), 2)}`
📉 Avg Loss: `{safe_round(safe_get(stats, 'avg_loss', 0), 2)}`

🔥 Max DD: `{safe_get(stats, 'max_drawdown', 0)}%`
"""

    def send_stats(self, stats: Dict):
        self.send_message(self.format_stats(stats))

    # =========================
    # 📊 TRADE RESULT
    # =========================
    def send_trade_result(self, trade: Dict, symbol: str):

        try:
            result = trade.get("result", "UNKNOWN")
            result_emoji = "🟢" if result == "WIN" else "🔴"

            strategy = trade.get("strategy", "unknown")
            emoji = STRATEGY_EMOJI.get(strategy, "📊")

            msg = f"""
📊 *TRADE CLOSED*

{emoji} `{strategy.upper()}`
{result_emoji} {trade.get('side')} — {symbol}

💰 PnL: `{safe_round(trade.get('pnl', 0), 2)}`
📍 Entry: `{format_price(trade.get('entry'))}`

━━━━━━━━━━━━━━━
"""

            logger.info(f"Sending trade result: {symbol} | {result}")
            self.send_message(msg)

        except Exception as e:
            logger.error(f"Trade result formatting error: {e}")

    # =========================
    # 📥 POLL UPDATES
    # =========================
    def _poll_updates(self):
        while True:
            try:
                url = f"{self.base_url}/getUpdates"
                params = {"offset": self.last_update_id + 1, "timeout": 30}
                response = requests.get(url, params=params, timeout=35)

                if response.status_code == 200:
                    updates = response.json().get("result", [])
                    for update in updates:
                        self._handle_update(update)
                        self.last_update_id = update["update_id"]
                else:
                    logger.warning(f"Poll failed: {response.status_code}")

            except Exception as e:
                logger.error(f"Polling error: {e}")

            time.sleep(1)

    # =========================
    # 🎛️ HANDLE UPDATE
    # =========================
    def _handle_update(self, update: Dict):
        message = update.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")

        if chat_id != self.chat_id:
            logger.debug(f"Ignoring command from unauthorized chat: {chat_id}")
            return

        if text.startswith("/"):
            logger.info(f"Stats command received: {text}")
            command = text.split()[0]
            self._handle_command(command)

    # =========================
    # 🎛️ HANDLE COMMAND
    # =========================
    def _handle_command(self, command: str):
        if command == "/stats":
            self._cmd_stats()
        elif command == "/equity":
            self._cmd_equity()
        elif command == "/best":
            self._cmd_best()
        elif command == "/status":
            self._cmd_status()
        elif command == "/trades":
            self._cmd_trades()
        elif command == "/help":
            self._cmd_help()
        else:
            self.send_message("Unknown command. Use /help")

    # =========================
    # 📊 /STATS
    # =========================
    def _cmd_stats(self):
        try:
            trades = self.repo.get_trades()  # Get all trades
            closed = [t for t in trades if t.get("status") == "CLOSED"]
            if not closed:
                self.send_message("📊 *No closed trades yet*\n\nWait for trades to close to see stats.")
                return
            stats = Stats(closed).summary()
            self.send_stats(stats)
        except Exception as e:
            logger.error(f"/stats error: {e}")
            self.send_message("Error retrieving stats")

    # =========================
    # 📈 /EQUITY
    # =========================
    def _cmd_equity(self):
        try:
            history = self.repo.get_balance_history(limit=10)
            if history:
                msg = "📈 *Equity Curve (Last 10)*\n"
                for i, bal in enumerate(history, 1):
                    msg += f"{i}. ${bal:.2f}\n"
                self.send_message(msg)
            else:
                self.send_message("📈 No equity data yet")
        except Exception as e:
            logger.error(f"/equity error: {e}")
            self.send_message("❌ Equity error")

    # =========================
    # 🏆 /BEST
    # =========================
    def _cmd_best(self):
        try:
            best = self.repo.get_best_performers(limit=5)
            if best:
                msg = "🏆 *Top Performers*\n"
                for p in best:
                    msg += f"• {p['symbol']}: ${p['total_pnl']:.2f} ({p['trade_count']} trades)\n"
                self.send_message(msg)
            else:
                self.send_message("📊 No performance data yet")
        except Exception as e:
            logger.error(f"/best error: {e}")
            self.send_message("❌ Best performers error")

    # =========================
    # 📊 /STATUS
    # =========================
    def _cmd_status(self):
        try:
            active = self.repo.get_active_trades()
            last_balance = self.repo.get_last_balance()
            msg = f"🟢 Active trades: {len(active)}\n"
            if last_balance:
                msg += f"💰 Balance: ${last_balance:.2f}"
            self.send_message(msg)
        except Exception as e:
            logger.error(f"/status error: {e}")
            self.send_message("❌ Status error")

    # =========================
    # 📊 /TRADES
    # =========================
    def _cmd_trades(self):
        try:
            all_trades = self.repo.get_trades()
            closed = [t for t in all_trades if t.get("status") == "CLOSED"]
            recent = closed[-5:] if len(closed) >= 5 else closed
            if recent:
                msg = "📊 *Recent Closed Trades*\n"
                for t in recent:
                    result = t.get("result", "UNKNOWN")
                    emoji = "🟢" if result == "WIN" else "🔴"
                    msg += f"{emoji} {t['symbol']} {t['side']}: ${t.get('pnl', 0):.2f}\n"
                self.send_message(msg)
            else:
                self.send_message("📭 No closed trades yet")
        except Exception as e:
            logger.error(f"/trades error: {e}")
            self.send_message("❌ Trades error")

    # =========================
    # ❓ /HELP
    # =========================
    def _cmd_help(self):
        msg = """
🤖 *Bot Commands*

/stats - Current performance stats
/equity - Equity curve snapshot
/best - Top-performing coin/strategy pairs
/status - Current active trades and balance
/trades - Recent closed trades
/help - This help message
        """
        self.send_message(msg)

    # =========================
    # ⏰ PERIODIC STATS
    # =========================
    def _periodic_stats(self):
        """Send hourly stats summary."""
        while True:
            time.sleep(self.stats_interval)
            try:
                trades = self.repo.get_trades()
                closed = [t for t in trades if t.get("status") == "CLOSED"]
                if closed:
                    stats = Stats(closed).summary()
                    msg = self.format_stats(stats)
                else:
                    msg = "📊 *Hourly Update*\nNo closed trades yet."
                self.send_message(msg)
            except Exception as e:
                logger.error(f"Periodic stats error: {e}")