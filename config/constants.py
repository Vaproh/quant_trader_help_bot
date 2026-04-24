# =========================
# 🪙 DEFAULT SYMBOLS
# =========================
DEFAULT_SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT"
]

PREFERENCE_SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT"
]

# =========================
# ⏱️ TIME CONSTANTS (SECONDS)
# =========================
SECOND = 1
MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR

# =========================
# 📊 DEFAULT INTERVALS
# =========================
DEFAULT_TIMEFRAMES = [
    "1m",
    "5m",
    "15m",
    "1h",
    "4h",
    "1d"
]

# =========================
# ⚠️ RISK MANAGEMENT
# =========================
DEFAULT_RISK_PER_TRADE = 0.02
MAX_OPEN_TRADES = 5

# Leverage caps
MAIN_BOT_MAX_LEVERAGE = 5
EXTENSION_MAX_LEVERAGE = 10

# =========================
# 🧠 DECISION SYSTEM
# =========================
MIN_CONFIDENCE = 50
WATCHLIST_MIN_CONFIDENCE = 55

# =========================
# 📡 API CONFIG
# =========================
API_TIMEOUT = 5  # seconds
API_RETRIES = 3

# =========================
# 🧠 NEWS SYSTEM
# =========================
NEWS_FETCH_INTERVAL = 10 * MINUTE  # cache duration

# =========================
# 📉 ORDER BOOK
# =========================
ORDERBOOK_LIMIT = 50

# =========================
# 💾 CACHE SETTINGS
# =========================
CACHE_DEFAULT_TTL = 30  # seconds
CACHE_MARKET_TTL = 10   # candles update fast
CACHE_ORDERBOOK_TTL = 5
CACHE_NEWS_TTL = 600    # 10 minutes

# =========================
# 📊 CHART SETTINGS
# =========================
CHART_OUTPUT_DIR = "charts/output"

# =========================
# 🤖 TELEGRAM
# =========================
TELEGRAM_RETRIES = 3

# =========================
# 🧪 SYSTEM FLAGS
# =========================
DEBUG_MODE = True
DRY_RUN = True  # no real trading (always ON for now)