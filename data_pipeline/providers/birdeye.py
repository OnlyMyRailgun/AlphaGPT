import aiohttp
import asyncio
from datetime import datetime, timedelta
from loguru import logger
from ..config import Config
from .base import DataProvider

class BirdeyeProvider(DataProvider):
    def __init__(self):
        self.provider_name = "birdeye"
        self.base_url = "https://public-api.birdeye.so"
        self.session_headers = {
            "X-API-KEY": Config.BIRDEYE_API_KEY,
            "accept": "application/json",
            "x-chain": "solana"
        }
        self.headers = self.session_headers
        self.semaphore = asyncio.Semaphore(Config.CONCURRENCY)
        self.request_interval = 1.0 / Config.BIRDEYE_RPS if Config.BIRDEYE_RPS > 0 else 0.0

    async def _sleep_for_rate_limit(self):
        if self.request_interval > 0:
            await asyncio.sleep(self.request_interval)

    async def _fetch_trending_page(self, session, url, params):
        attempts = 0
        while True:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()

                if resp.status == 429 and attempts < Config.BIRDEYE_RETRY_LIMIT:
                    attempts += 1
                    logger.warning(
                        f"Birdeye trending 429 at offset={params['offset']}, retry {attempts}/{Config.BIRDEYE_RETRY_LIMIT}"
                    )
                    await self._sleep_for_rate_limit()
                    continue

                logger.error(f"Birdeye Trending Error: {resp.status}")
                return None
        
    async def get_trending_tokens(self, limit=100):
        url = f"{self.base_url}/defi/token_trending"

        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                results = []
                offset = 0

                while len(results) < limit:
                    page_limit = min(limit - len(results), 20)
                    params = {
                        "sort_by": "rank",
                        "sort_type": "asc",
                        "offset": offset,
                        "limit": page_limit,
                    }

                    data = await self._fetch_trending_page(session, url, params)
                    if data is None:
                        return results

                    raw_list = data.get('data', {}).get('tokens', [])
                    if not raw_list:
                        break

                    for t in raw_list:
                        results.append({
                            'address': t['address'],
                            'symbol': t.get('symbol', 'UNKNOWN'),
                            'name': t.get('name', 'UNKNOWN'),
                            'decimals': t.get('decimals', 6),
                            'liquidity': t.get('liquidity', 0),
                            'fdv': t.get('fdv', 0)
                        })

                    if len(raw_list) < page_limit:
                        break
                    offset += len(raw_list)
                    await self._sleep_for_rate_limit()

                return results
            except Exception as e:
                logger.error(f"Birdeye Trending Exception: {e}")
                return []

    async def get_token_history(self, session, address, days=Config.HISTORY_DAYS):
        time_to = int(datetime.now().timestamp())
        time_from = int((datetime.now() - timedelta(days=days)).timestamp())
        url = f"{self.base_url}/defi/ohlcv"
        params = {
            "address": address,
            "type": Config.TIMEFRAME,
            "time_from": time_from,
            "time_to": time_to
        }

        try:
            attempts = 0
            while True:
                async with self.semaphore:
                    async with session.get(url, params=params) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            items = data.get('data', {}).get('items', [])
                            if not items:
                                return []

                            formatted = []
                            for item in items:
                                formatted.append((
                                    datetime.fromtimestamp(item['unixTime']),
                                    address,
                                    float(item['o']),
                                    float(item['h']),
                                    float(item['l']),
                                    float(item['c']),
                                    float(item['v']),
                                    0.0,
                                    0.0,
                                    'birdeye'
                                ))
                            await self._sleep_for_rate_limit()
                            return formatted

                        if resp.status == 429 and attempts < Config.BIRDEYE_RETRY_LIMIT:
                            attempts += 1
                            logger.warning(
                                f"Birdeye 429 for {address}, retrying in 5s... ({attempts}/{Config.BIRDEYE_RETRY_LIMIT})"
                            )
                        else:
                            return []

                await asyncio.sleep(5)
                await self._sleep_for_rate_limit()
        except Exception as e:
            logger.error(f"Birdeye Fetch Error {address}: {e}")
            return []
