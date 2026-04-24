SETTINGS = {

    # =========================
    # 🪙 SYMBOLS
    # =========================
    "symbols": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"],

    "preference_coins": ["BTC/USDT", "ETH/USDT"],

    # =========================
    # ⏱️ LOOP
    # =========================
    "loop_interval": 10,

    # =========================
    # ⚠️ RISK
    # =========================
    "risk_per_trade": 0.02,

    # =========================
    # 🧠 DECISION
    # =========================
    "decision": {
        "min_confidence": 50,
        "max_leverage": 5
    },

    # =========================
    # 📊 STRATEGY DECIDER
    # =========================
    "strategy_decider": {
        "max_signals_per_cycle": 3
    },

    # =========================
    # 📈 STRATEGIES CONFIG
    # =========================
    "strategies": {
        "enabled": [
            "breakout",
            "pullback",
            "range",
            "overnight"
        ]
    },

    # =========================
    # ⚙️ EXECUTION
    # =========================
    "paper_trader": {
        "initial_balance": 100.0,
        "max_open_trades": 5
    },

    # =========================
    # 📊 CHARTS
    # =========================
    "charts": {
        "output_dir": "charts/output"
    },

    # =========================
    # ⚡ EXTENSION BOT
    # =========================
    "extension": {
        "loop_interval": 5,
        "risk_per_trade": 0.05,
        "max_leverage": 10,
        "max_signals_per_cycle": 5
    },

    # =========================
    # 👀 WATCHLIST
    # =========================
    "watchlist": {
        "symbols": [],
        "min_confidence": 55,
        "max_signals_per_cycle": 2
    }
}