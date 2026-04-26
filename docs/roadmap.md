# 🔥 Trading Bot Roadmap

> **Current Status:** Phase 1 (Stabilization & Core Fixes)  
> **Objective:** Transition from a basic signal bot to a high-intelligence market execution engine.

---

## 🛠 PHASE 1: System Stabilization (Immediate)
*Focus: Eliminating silent failures, ensuring execution reliability, and cleaning up signal logic.*

### 🔴 Critical Reliability Fixes
- [ ] **Telegram Connectivity:** Detect API failures/rate limits and implement retry mechanisms.
- [ ] **Dead-Drop Protection:** Add "Last Message Sent" watchdog; trigger alerts if the bot is alive but silent.
- [ ] **Thread Safety:** Implement auto-restart for crashed threads and logging for silent failures.
- [ ] **State Persistence:** Ensure trades actually close and TP/SL values are tracked across restarts.

### 🧠 Signal & Strategy Logic
- [ ] **Deduplication:** Replace strategy-based skip logic with trade-based detection (prevent duplicate entries on the same setup).
- [ ] **Confidence Normalization:** Standardize confidence scores across all strategies (prevent 50% spam or fake 100% inflation).
- [ ] **Dynamic Cooldowns:** Implement per-symbol (10-20m) and per-direction (Long/Short) cooldowns to prevent flip-trade spam.
- [ ] **Field Validation:** Ensure every strategy returns: `strategy_name`, `confidence`, and `reason`.

### 📊 Core Analytics (Stats v1)
- [ ] **Performance Tracking:** Track win/loss streaks and max drawdown.
- [ ] **Time-Based Reports:** Automated stats every 1 hour and a daily performance summary.
- [ ] **Equity Tracking:** Basic equity curve logging.

---

## 🧠 PHASE 2: Intelligent Market Engine
*Focus: Context-awareness, multi-timeframe confluence, and dynamic coin selection.*

### ⚡ Market Regime & Scanning
- [ ] **Regime Detection:** Implement engine to distinguish between Trending vs. Ranging markets.
- [ ] **Volatility Filter:** Automatically switch strategies or skip trading during "Chop Zones" or low liquidity.
- [ ] **Global Scanner:** - **Global Scan (30m):** Find top movers and volume spikes across the entire market.
    - **Active Pool (~20 coins):** Continuously monitor high-potential assets.
    - **Hot List (~5 coins):** Highest priority for immediate signal execution.

### 🎯 Confluence & Execution
- [ ] **Multi-Timeframe (MTF) Analysis:**
    - `1m` for entries, `15m` for structure, `1h/4h` for macro bias.
- [ ] **Confluence Scoring:** Weighted scoring based on RSI alignment, Volume confirmation, and Trend alignment.
- [ ] **Smart Filtering:** Auto-skip conflicting signals (e.g., Long signal on 1m vs. Heavy Resistance on 15m).

### 📈 Enhanced Visualization
- [ ] **Telegram Charting:** Generate and send charts with annotated Entry, SL, and TP levels.
- [ ] **Dashboard Commands:**
    - `/stats` — Current session performance.
    - `/equity` — Visual equity curve snapshot.
    - `/best` — Identify top-performing coin/strategy pairs.

---

## 🚀 PHASE 3: Alpha Listing Engine
*Focus: High-edge trading on new listings and narrative-driven momentum.*

### 🔍 Listing Detection
- [ ] **Exchange Scrapers:** Track Binance/KuCoin announcements for new Spot and Futures listings.
- [ ] **Hype Scoring:** Factor in narrative (AI, RWA, etc.), social volume, and exchange presence.

### 📉 Listing Entry Logic
- [ ] **Post-Pump Stabilization:** Logic to detect the first support hold after the initial listing pump.
- [ ] **Volume Expansion:** Detect "Secondary Wave" entries based on volume profile.
- [ ] **Risk Guardrails:** Auto-skip pumps >80% or assets with predatory tokenomics.

---

## 🚩 Priority Order
1.  **Silence Protection:** Finalize the Telegram watchdog (Bot must never be silent without an alert).
2.  **Trade Frequency:** Tighten cooldowns and deduplication to preserve capital.
3.  **Confidence Quality:** Minimum 60% buffer implementation.
4.  **Intelligence:** Begin Phase 2 "Market Regime" engine.

---

### 🔄 Coin Lifecycle State Machine
`WATCHING` → `HOT` → `TRADEABLE` → `COOLING` → `DEAD`

---
