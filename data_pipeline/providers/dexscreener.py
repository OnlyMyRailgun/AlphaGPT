import aiohttp
import asyncio
from datetime import datetime, timedelta
from loguru import logger
from .base import DataProvider
from ..config import Config

class DexScreenerProvider(DataProvider):
    def __init__(self):
        self.provider_name = "dexscreener"
        self.base_url = Config.DEXSCREENER_API_BASE.rstrip("/")
        self.chart_api_url = Config.DEXSCREENER_CHART_API_URL.rstrip("/")
        self.session_headers = {"accept": "application/json"}
        self.semaphore = asyncio.Semaphore(Config.CONCURRENCY)

    async def _get_json(self, session, url, params=None):
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                raise aiohttp.ClientResponseError(
                    request_info=resp.request_info,
                    history=resp.history,
                    status=resp.status,
                    message=await resp.text(),
                    headers=resp.headers,
                )
            return await resp.json()

    def _normalize_pairs(self, pairs, token_address=None):
        best_token = None
        best_liquidity = -1.0

        for pair in pairs or []:
            if pair.get("chainId") != Config.CHAIN:
                continue

            base_token = pair.get("baseToken") or {}
            quote_token = pair.get("quoteToken") or {}
            base_address = base_token.get("address")
            quote_address = quote_token.get("address")

            if token_address:
                if base_address == token_address:
                    target_token = base_token
                elif quote_address == token_address:
                    target_token = quote_token
                else:
                    continue
            else:
                target_token = base_token

            liquidity = float((pair.get("liquidity") or {}).get("usd") or 0.0)
            if liquidity <= best_liquidity:
                continue

            best_liquidity = liquidity
            best_token = {
                "address": target_token.get("address", token_address or ""),
                "symbol": target_token.get("symbol", "UNKNOWN"),
                "name": target_token.get("name", "UNKNOWN"),
                "liquidity": liquidity,
                "fdv": float(pair.get("fdv") or 0.0),
                "decimals": int(target_token.get("decimals") or 6),
                "pair_address": pair.get("pairAddress", ""),
            }

        return best_token

    def _normalize_candles(self, payload, address, token_snapshot):
        items = (
            payload.get("bars")
            or payload.get("candles")
            or payload.get("data", {}).get("bars", [])
            or payload.get("data", {}).get("candles", [])
        )
        if not items:
            return []

        liquidity = float(token_snapshot.get("liquidity") or 0.0)
        fdv = float(token_snapshot.get("fdv") or 0.0)

        records = []
        for item in items:
            ts = item.get("timestamp") or item.get("time") or item.get("ts") or item.get("t")
            if ts is None:
                continue
            records.append(
                (
                    datetime.fromtimestamp(int(ts)),
                    address,
                    float(item.get("open") or item.get("o") or 0.0),
                    float(item.get("high") or item.get("h") or 0.0),
                    float(item.get("low") or item.get("l") or 0.0),
                    float(item.get("close") or item.get("c") or 0.0),
                    float(item.get("volume") or item.get("v") or 0.0),
                    liquidity,
                    fdv,
                    self.provider_name,
                )
            )
        return records
    
    async def get_trending_tokens(self, limit=50):
        url = f"{self.base_url}/token-boosts/top/v1"
        async with aiohttp.ClientSession(headers=self.session_headers) as session:
            try:
                payload = await self._get_json(session, url)
            except Exception as exc:
                logger.error(f"DexScreener trending error: {exc}")
                return []

            addresses = []
            seen = set()
            for item in payload or []:
                if item.get("chainId") != Config.CHAIN:
                    continue
                address = item.get("tokenAddress")
                if not address or address in seen:
                    continue
                seen.add(address)
                addresses.append(address)
                if len(addresses) >= limit:
                    break

            if not addresses:
                return []

            return await self.get_token_details_batch(session, addresses)

    async def get_token_details_batch(self, session, addresses):
        valid_data = []
        for address in addresses:
            url = f"{self.base_url}/token-pairs/v1/{Config.CHAIN}/{address}"
            try:
                pairs = await self._get_json(session, url)
                normalized = self._normalize_pairs(pairs, token_address=address)
                if normalized:
                    valid_data.append(normalized)
            except Exception as exc:
                logger.error(f"DexScreener token details error for {address}: {exc}")
        return valid_data

    async def get_token_history(self, session, address, days):
        pair_url = f"{self.base_url}/token-pairs/v1/{Config.CHAIN}/{address}"
        try:
            pairs = await self._get_json(session, pair_url)
            token_snapshot = self._normalize_pairs(pairs, token_address=address)
            if not token_snapshot or not token_snapshot.get("pair_address"):
                return []

            time_to = int(datetime.now().timestamp())
            time_from = int((datetime.now() - timedelta(days=days)).timestamp())
            chart_url = f"{self.chart_api_url}/{Config.CHAIN}/{token_snapshot['pair_address']}"
            params = {"from": time_from, "to": time_to, "resolution": Config.TIMEFRAME}

            async with self.semaphore:
                payload = await self._get_json(session, chart_url, params=params)
            return self._normalize_candles(payload, address, token_snapshot)
        except Exception as exc:
            logger.warning(f"DexScreener history unavailable for {address}: {exc}")
            return []
