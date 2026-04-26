import requests
import time
import threading
from typing import List, Dict

from utils.logger import get_logger
from config.secrets import SECRETS
from storage.repository import Repository


logger = get_logger(__name__)

# =========================
# 🎨 STRATEGY EMOJIS
# =========================
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


class TelegramWatchlistBot:

    def __init__(self, repo: Repository = None):
        self.token = SECRETS["telegram_watchlist_token"]
        self.chat_id = int(SECRETS["telegram_watchlist_chat_id"])
        self.base_url = f"https://api.telegram.org/bot{self.token}"

        self.repo = repo or Repository()
        self.watchlist: List[str] = self.repo.get_watchlist()

        self.last_update_id = 0
        self.polling_thread = threading.Thread(target=self._poll_updates, daemon=True)
        self.polling_thread.start()

    # =========================
    # 📤 SEND MESSAGE
    # =========================
    def send_message(self, text: str):
        try:
            url = f"{self.base_url}/sendMessage"

            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }

            for attempt in range(3):
                try:
                    res = requests.post(url, json=payload, timeout=10)

                    if res.status_code == 200:
                        logger.info("Watchlist message sent")
                        return True
                    else:
                        logger.warning(f"Watchlist failed [{res.status_code}]: {res.text}")
                except Exception as e:
                    logger.error(f"Watchlist send error (attempt {attempt+1}): {e}")

            logger.error("Watchlist message FAILED after retries")
            return False

        except Exception as e:
            logger.error(f"Watchlist send error: {e}")

    # =========================
    # 📤 SEND IMAGE
    # =========================
    def send_image(self, image_path: str, caption: str = ""):

        url = f"{self.base_url}/sendPhoto"

        for attempt in range(3):
            try:
                with open(image_path, "rb") as img:
                    files = {"photo": img}
                    data = {
                        "chat_id": self.chat_id,
                        "caption": caption,
                        "parse_mode": "Markdown"
                    }

                    response = requests.post(url, files=files, data=data, timeout=15)

                    if response.status_code == 200:
                        logger.info("Watchlist image sent")
                        return True
                    else:
                        logger.warning(f"Watchlist image failed [{response.status_code}]: {response.text}")

            except Exception as e:
                logger.error(f"Watchlist image error (attempt {attempt+1}): {e}")

        logger.error("Watchlist image FAILED after retries")
        return False

    # =========================
    # 📊 FORMAT SETUP
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
                    logger.warning(f"Watchlist poll failed: {response.status_code}")

            except Exception as e:
                logger.error(f"Watchlist polling error: {e}")

            time.sleep(1)

    # =========================
    # 🎛️ HANDLE UPDATE
    # =========================
    def _handle_update(self, update: Dict):
        message = update.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")

        if chat_id != self.chat_id:
            logger.debug(f"Watchlist: unauthorized chat {chat_id}")
            return

        if text.startswith("/"):
            logger.info(f"Watchlist command received: {text}")
            command = text.split()
            cmd = command[0]
            args = command[1:] if len(command) > 1 else []
            self._handle_command(cmd, args)

    # =========================
    # 🎛️ HANDLE COMMAND
    # =========================
    def _handle_command(self, cmd: str, args: List[str]):
        if cmd == "/add" and args:
            self.add_coin(args[0])
        elif cmd == "/remove" and args:
            self.remove_coin(args[0])
        elif cmd == "/list":
            self.show_watchlist()
        elif cmd == "/help":
            self._cmd_help()
        else:
            self.send_message("Unknown command. Use /help")

    # =========================
    # ❓ /HELP
    # =========================
    def _cmd_help(self):
        msg = """
👀 *Watchlist Commands*

/add <SYMBOL> - Add coin to watchlist
/remove <SYMBOL> - Remove coin from watchlist
/list - Show current watchlist
/help - This help message
        """
        self.send_message(msg)

    # =========================
    # 📊 FORMAT SETUP
    # =========================
    # ➕ ADD COIN
    # =========================
    def add_coin(self, symbol: str):
        symbol = symbol.upper()

        if self.repo.add_to_watchlist(symbol):
            if symbol not in self.watchlist:
                self.watchlist.append(symbol)
            self.send_message(f"✅ Added `{symbol}` to watchlist")
        else:
            self.send_message(f"⚠️ `{symbol}` already in watchlist or error")

    # =========================
    # ➖ REMOVE COIN
    # =========================
    def remove_coin(self, symbol: str):
        symbol = symbol.upper()

        if self.repo.remove_from_watchlist(symbol):
            if symbol in self.watchlist:
                self.watchlist.remove(symbol)
            self.send_message(f"❌ Removed `{symbol}`")
        else:
            self.send_message(f"⚠️ `{symbol}` not found or error")

    # =========================
    # 📋 SHOW WATCHLIST
    # =========================
    def show_watchlist(self):

        if not self.watchlist:
            self.send_message("📭 Watchlist is empty")
            return

        coins = "\n".join([f"• {c}" for c in self.watchlist])

        msg = f"""
👀 *WATCHLIST*

{coins}
"""
        self.send_message(msg)

    # =========================
    # 📋 GET WATCHLIST
    # =========================
    def get_watchlist(self) -> List[str]:
        return self.watchlist.copy()

    # =========================
    # 📊 FORMAT SETUP
    # =========================
    def format_setup(self, trade: Dict, symbol: str) -> str:

        if trade["action"] != "TRADE":
            return ""

        strategy = trade.get("strategy", "unknown")
        emoji = STRATEGY_EMOJI.get(strategy, "📊")

        side_emoji = "🟢" if trade["side"] == "LONG" else "🔴"

        return f"""
👀 *WATCHLIST SETUP*

{emoji} *{strategy.upper()}*
{side_emoji} *{trade['side']}* — {symbol}

📍 Entry: `{trade['entry']:.4f}`
🛑 SL: `{trade['stop_loss']:.4f}`
🎯 TP: `{trade['take_profit']:.4f}`

🧠 Confidence: `{trade['confidence']}%`

━━━━━━━━━━━━━━━
“Patience prints money.”
"""

    # =========================
    # 📤 SEND SETUP
    # =========================
    def send_setup(self, trade: Dict, symbol: str, chart_path: str = None):

        msg = self.format_setup(trade, symbol)

        if not msg:
            return

        if chart_path:
            self.send_image(chart_path, msg)
        else:
            self.send_message(msg)