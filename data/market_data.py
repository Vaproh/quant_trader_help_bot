import requests
from typing import List, Optional, Dict

from utils.logger import get_logger
from config.constants import API_TIMEOUT, API_RETRIES, CACHE_MARKET_TTL, ORDERBOOK_LIMIT
from storage.cache import Cache
from data.order_book import OrderBook


logger = get_logger(__name__)


class MarketData:

    def __init__(self, base_url: str = "https://api.binance.com", cache: Optional[Cache] = None):
        self.base_url = base_url
        self.cache = cache or Cache()

    # =========================
    # 📊 FETCH KLINES (MAIN)
    # =========================
    def get_klines(
        self,
        symbol: str,
        interval: str = "1m",
        limit: int = 100
    ) -> List[List[float]]:

        cache_key = f"klines:{symbol}:{interval}:{limit}"

        # =========================
        # CACHE CHECK
        # =========================
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"[CACHE HIT] {cache_key}")
            return cached

        logger.info(f"[FETCH] Fetching klines for {symbol} ({interval})")

        clean_symbol = symbol.replace("/", "").upper()

        url = (
            f"{self.base_url}/api/v3/klines"
            f"?symbol={clean_symbol}"
            f"&interval={interval}"
            f"&limit={limit}"
        )

        # =========================
        # RETRY LOGIC
        # =========================
        for attempt in range(1, API_RETRIES + 1):
            try:
                response = requests.get(url, timeout=API_TIMEOUT)

                logger.info(f"[HTTP] {response.status_code} | Attempt {attempt}")

                if response.status_code != 200:
                    logger.warning(f"[ERROR] Bad status: {response.status_code}")
                    continue

                data = response.json()

                # =========================
                # VALIDATION
                # =========================
                if not isinstance(data, list) or len(data) == 0:
                    raise ValueError("Invalid kline data format")

                candles = self._parse_klines(data)

                if not candles:
                    raise ValueError("Parsed candles empty")

                # =========================
                # CACHE STORE
                # =========================
                self.cache.set(cache_key, candles, CACHE_MARKET_TTL)

                logger.info(f"[SUCCESS] Retrieved {len(candles)} candles")

                return candles

            except requests.exceptions.Timeout:
                logger.warning(f"[TIMEOUT] Attempt {attempt}")

            except requests.exceptions.ConnectionError:
                logger.warning(f"[CONNECTION ERROR] Attempt {attempt}")

            except Exception as e:
                logger.error(f"[UNEXPECTED ERROR] {e}")

        # =========================
        # HARD FAIL (NO SILENT FAIL)
        # =========================
        raise Exception(f"Failed to fetch market data for {symbol}")

    # =========================
    # 🔄 PARSE DATA
    # =========================
    def _parse_klines(self, raw_data: List) -> List[List[float]]:
        parsed = []

        try:
            for k in raw_data:
                parsed.append([
                    float(k[0]),  # timestamp
                    float(k[1]),  # open
                    float(k[2]),  # high
                    float(k[3]),  # low
                    float(k[4]),  # close
                    float(k[5])   # volume
                ])

            return parsed

        except Exception as e:
            logger.error(f"[PARSE ERROR] {e}")
            return []

    # =========================
    # 📈 CLOSE PRICES
    # =========================
    def get_closes(self, symbol: str, interval: str = "1m", limit: int = 100) -> List[float]:
        candles = self.get_klines(symbol, interval, limit)
        return [c[4] for c in candles]

    # =========================
    # 📊 HIGHS
    # =========================
    def get_highs(self, symbol: str, interval: str = "1m", limit: int = 100) -> List[float]:
        candles = self.get_klines(symbol, interval, limit)
        return [c[2] for c in candles]

    # =========================
    # 📉 LOWS
    # =========================
    def get_lows(self, symbol: str, interval: str = "1m", limit: int = 100) -> List[float]:
        candles = self.get_klines(symbol, interval, limit)
        return [c[3] for c in candles]

    # =========================
    # 📊 CURRENT PRICE (TICKER)
    # =========================
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Get current price and 24h stats.
        Returns: {"price": float, "change": float, "volume": float, ...}
        """

        cache_key = f"ticker:{symbol}"

        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"[CACHE HIT] {cache_key}")
            return cached

        logger.info(f"[FETCH] Ticker for {symbol}")

        clean_symbol = symbol.replace("/", "").upper()

        url = f"{self.base_url}/api/v3/ticker/24hr?symbol={clean_symbol}"

        for attempt in range(API_RETRIES):
            try:
                response = requests.get(url, timeout=API_TIMEOUT)

                if response.status_code == 200:
                    data = response.json()
                    parsed = {
                        "price": float(data.get("lastPrice", 0)),
                        "change": float(data.get("priceChangePercent", 0)),
                        "volume": float(data.get("volume", 0)),
                        "high": float(data.get("highPrice", 0)),
                        "low": float(data.get("lowPrice", 0))
                    }

                    self.cache.set(cache_key, parsed, CACHE_MARKET_TTL)
                    return parsed

                else:
                    logger.warning(f"[TICKER FAIL] {response.status_code}: {response.text}")

            except Exception as e:
                logger.error(f"[TICKER ERROR] Attempt {attempt+1}: {e}")

        return None

    # =========================
    # 📋 ORDER BOOK
    # =========================
    def get_orderbook(self, symbol: str, limit: int = ORDERBOOK_LIMIT) -> Optional[Dict]:
        """
        Get order book snapshot.
        Returns: {"bids": [[price, qty], ...], "asks": [[price, qty], ...]}
        """

        orderbook_fetcher = OrderBook(base_url=self.base_url, cache=self.cache)
        bids, asks = orderbook_fetcher.get_order_book(symbol, limit)

        if bids and asks:
            return {"bids": bids, "asks": asks}
        return None

    # =========================
    # ⚖️ ORDER BOOK PRESSURE
    # =========================
    def get_orderbook_pressure(self, symbol: str) -> str:
        """
        Analyze order book pressure.
        Returns: "BUY_PRESSURE", "SELL_PRESSURE", or "NEUTRAL"
        """

        orderbook_fetcher = OrderBook(base_url=self.base_url, cache=self.cache)
        return orderbook_fetcher.get_pressure(symbol)