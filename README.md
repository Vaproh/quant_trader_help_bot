# 🤖 Quant Trade Helper Bot

A modular, multi-engine crypto trading system for **Binance (USDT-M + Spot)** with:

- 📊 Technical analysis
- 🧠 AI sentiment analysis
- ⚡ Multi-strategy execution
- 📡 Telegram signal bots
- 💾 SQLite persistence
- 📈 Performance tracking

---

## 🚀 Features

### 🧠 Core System
- Multi-symbol trading (BTC, ETH, BNB, SOL by default)
- Strategy-based decision engine
- Risk-managed position sizing
- Trade lifecycle tracking (open → close → PnL)

### ⚡ Engines
- **Main Engine** → disciplined trades
- **Extension Engine** → high-risk / high-reward
- **Watchlist Engine** → custom coin sniper

### 📡 Telegram Bots
- `telegram_main` → trade signals
- `telegram_stats` → performance stats
- `telegram_extension` → aggressive setups
- `telegram_watchlist` → custom coin alerts

### 💾 Database
- SQLite (`trading.db`)
- Stores:
  - Trades
  - Balance history

### 📊 Charts & Stats
- Equity curve
- Drawdown
- PnL distribution
- Win rate, profit factor


---

## ⚙️ Installation

### 1️⃣ Clone repo
```bash
git clone <your-repo>
cd quant_trade_helper_bot
```

2️⃣ Create virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

---

🔐 Environment Variables (.env)

Create a .env file in root:

```env
# TELEGRAM
telegram_main_token=
telegram_main_chat_id=

telegram_extension_token=
telegram_extension_chat_id=

telegram_watchlist_token=
telegram_watchlist_chat_id=

telegram_stats_token=
telegram_stats_chat_id=

# APIs
news_api_key=
ai_api_key=

# (optional)
binance_api_key=
binance_secret_key=
```
---

▶️ Run the Bot
```bash
python main.py
```
---

🧠 How It Works

```
Runner
 ├── Main Engine
 ├── Extension Engine
 └── Watchlist Engine
 ```

```
Each Engine:
 → PaperTrader
 → TradeManager
 → Repository (DB)
 → Telegram Bots
```


---

## ⚙️ Configuration

Edit:

config/settings.py

Examples:

Symbols

"symbols": ["BTC/USDT", "ETH/USDT"]

Risk

"risk_per_trade": 0.02

Extension Mode

"extension": {
    "max_leverage": 10
}


---

## 👀 Watchlist

Add custom coins in future DB integration or manually:

"watchlist": {
    "symbols": ["SOL/USDT", "PEPE/USDT"]
}


---

## 📊 Output

Logs

Console logs with trade activity


Database

trading.db


Charts

charts/output/



---

## 🧪 Mode

DRY_RUN = True

👉 Always ON (no real trading)


---

## 🧠 Strategy System

Currently includes:

Breakout

Pullback

Range

Momentum

Volume Spike

Pump

Fake Breakout

Overnight


👉 Strategies can be improved/extended.


---

🚧 Roadmap

[ ] Strategy optimization

[ ] Binance live trading

[ ] Web dashboard

[ ] Advanced risk engine

[ ] Backtesting module



---

⚠️ Disclaimer

This project is for educational and simulation purposes only.

Crypto markets are highly volatile.
You are fully responsible for any financial decisions.


---

💡 Philosophy

> “A fool admires complexity. A genius admires simplicity.”




