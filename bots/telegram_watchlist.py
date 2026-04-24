import requests
from typing import List, Dict

from utils.logger import get_logger
from config.secrets import SECRETS


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

    def __init__(self):
        self.token = SECRETS["telegram_watchlist_token"]
        self.chat_id = SECRETS["telegram_watchlist_chat_id"]

        self.base_url = f"https://api.telegram.org/bot{self.token}"

        # in-memory watchlist (later → DB)
        self.watchlist: List[str] = []

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

            res = requests.post(url, json=payload)

            if res.status_code != 200:
                logger.warning(f"Watchlist bot error: {res.text}")

        except Exception as e:
            logger.error(f"Watchlist send error: {e}")

    # =========================
    # ➕ ADD COIN
    # =========================
    def add_coin(self, symbol: str):
        symbol = symbol.upper()

        if symbol not in self.watchlist:
            self.watchlist.append(symbol)
            self.send_message(f"✅ Added `{symbol}` to watchlist")
        else:
            self.send_message(f"⚠️ `{symbol}` already in watchlist")

    # =========================
    # ➖ REMOVE COIN
    # =========================
    def remove_coin(self, symbol: str):
        symbol = symbol.upper()

        if symbol in self.watchlist:
            self.watchlist.remove(symbol)
            self.send_message(f"❌ Removed `{symbol}`")
        else:
            self.send_message(f"⚠️ `{symbol}` not found")

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
    def send_setup(self, trade: Dict, symbol: str):

        msg = self.format_setup(trade, symbol)

        if msg:
            self.send_message(msg)