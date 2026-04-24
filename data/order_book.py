import requests
from typing import Tuple, List, Optional

from utils.logger import get_logger
from config.constants import (
    API_TIMEOUT,
    API_RETRIES,
    ORDERBOOK_LIMIT,
    CACHE_ORDERBOOK_TTL
)
from storage.cache import Cache


logger = get_logger(__name__)


class OrderBook:

    def __init__(self, base_url: str = "https://api.binance.com", cache: Optional[Cache] = None):
        self.base_url = base_url
        self.cache = cache or Cache()

    # =========================
    # 📊 FETCH ORDER BOOK
    # =========================
    def get_order_book(
        self,
        symbol: str,
        limit: int = ORDERBOOK_LIMIT
    ) -> Tuple[List[List[float]], List[List[float]]]:

        cache_key = f"orderbook:{symbol}:{limit}"

        # ✅ 1. CACHE CHECK
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"OrderBook Cache HIT: {cache_key}")
            return cached

        logger.debug(f"OrderBook Cache MISS: {cache_key}")

        # ✅ 2. RETRY LOGIC
        for attempt in range(API_RETRIES):
            try:
                clean_symbol = symbol.replace("/", "")

                url = (
                    f"{self.base_url}/api/v3/depth"
                    f"?symbol={clean_symbol}"
                    f"&limit={limit}"
                )

                response = requests.get(url, timeout=API_TIMEOUT)

                if response.status_code != 200:
                    logger.warning(f"OrderBook bad response ({response.status_code}) for {symbol}")
                    continue

                data = response.json()

                bids = data.get("bids")
                asks = data.get("asks")

                # ✅ VALIDATION
                if not isinstance(bids, list) or not isinstance(asks, list):
                    logger.warning(f"Invalid orderbook structure for {symbol}")
                    continue

                parsed_bids, parsed_asks = self._parse(bids, asks)

                # ✅ CACHE STORE
                self.cache.set(
                    cache_key,
                    (parsed_bids, parsed_asks),
                    CACHE_ORDERBOOK_TTL
                )

                return parsed_bids, parsed_asks

            except requests.exceptions.RequestException as e:
                logger.warning(f"OrderBook network error (attempt {attempt+1}): {e}")

            except Exception as e:
                logger.error(f"OrderBook unexpected error: {e}")

        # ❌ FAIL SAFE
        logger.error(f"Failed to fetch order book for {symbol}")
        return [], []

    # =========================
    # 🔄 PARSE DATA
    # =========================
    def _parse(
        self,
        bids: List[List[str]],
        asks: List[List[str]]
    ) -> Tuple[List[List[float]], List[List[float]]]:

        try:
            parsed_bids = [[float(p), float(q)] for p, q in bids]
            parsed_asks = [[float(p), float(q)] for p, q in asks]

            return parsed_bids, parsed_asks

        except Exception as e:
            logger.error(f"OrderBook parse error: {e}")
            return [], []

    # =========================
    # ⚖️ PRESSURE ANALYSIS
    # =========================
    def get_pressure(self, symbol: str) -> str:

        bids, asks = self.get_order_book(symbol)

        if not bids or not asks:
            return "NEUTRAL"

        try:
            bid_volume = sum(q for _, q in bids)
            ask_volume = sum(q for _, q in asks)

            if bid_volume > ask_volume * 1.2:
                return "BUY_PRESSURE"

            elif ask_volume > bid_volume * 1.2:
                return "SELL_PRESSURE"

            else:
                return "NEUTRAL"

        except Exception as e:
            logger.error(f"Pressure calc error: {e}")
            return "NEUTRAL"