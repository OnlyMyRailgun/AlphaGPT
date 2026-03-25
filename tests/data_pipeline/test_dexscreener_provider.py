import asyncio
import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def reload_module(module_name: str):
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def load_provider(monkeypatch):
    monkeypatch.setenv("DATA_PROVIDER", "dexscreener")
    monkeypatch.setenv("BIRDEYE_API_KEY", "")
    reload_module("data_pipeline.config")
    provider_module = reload_module("data_pipeline.providers.dexscreener")
    return provider_module.DexScreenerProvider()


def test_get_trending_tokens_normalizes_highest_liquidity_pair(monkeypatch):
    provider = load_provider(monkeypatch)

    async def fake_get_json(session, url, params=None):
        if url.endswith("/token-boosts/top/v1"):
            return [
                {"chainId": "solana", "tokenAddress": "TokenA"},
                {"chainId": "solana", "tokenAddress": "TokenB"},
            ]
        if url.endswith("/token-pairs/v1/solana/TokenA"):
            return [
                {
                    "chainId": "solana",
                    "pairAddress": "PairA1",
                    "baseToken": {"address": "TokenA", "symbol": "AAA", "name": "Alpha", "decimals": 9},
                    "quoteToken": {"address": "USDC", "symbol": "USDC", "name": "USD Coin"},
                    "liquidity": {"usd": 1000},
                    "fdv": 5000,
                },
                {
                    "chainId": "solana",
                    "pairAddress": "PairA2",
                    "baseToken": {"address": "TokenA", "symbol": "AAA", "name": "Alpha", "decimals": 9},
                    "quoteToken": {"address": "SOL", "symbol": "SOL", "name": "Wrapped SOL"},
                    "liquidity": {"usd": 3500},
                    "fdv": 8000,
                },
            ]
        if url.endswith("/token-pairs/v1/solana/TokenB"):
            return [
                {
                    "chainId": "solana",
                    "pairAddress": "PairB1",
                    "baseToken": {"address": "TokenB", "symbol": "BBB", "name": "Beta"},
                    "quoteToken": {"address": "USDC", "symbol": "USDC", "name": "USD Coin"},
                    "liquidity": {"usd": 2200},
                    "fdv": 12000,
                }
            ]
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(provider, "_get_json", fake_get_json)
    tokens = asyncio.run(provider.get_trending_tokens(limit=2))

    assert tokens == [
        {
            "address": "TokenA",
            "symbol": "AAA",
            "name": "Alpha",
            "liquidity": 3500.0,
            "fdv": 8000.0,
            "decimals": 9,
            "pair_address": "PairA2",
        },
        {
            "address": "TokenB",
            "symbol": "BBB",
            "name": "Beta",
            "liquidity": 2200.0,
            "fdv": 12000.0,
            "decimals": 6,
            "pair_address": "PairB1",
        },
    ]


def test_get_token_history_normalizes_candles(monkeypatch):
    provider = load_provider(monkeypatch)

    async def fake_get_json(session, url, params=None):
        if url.endswith("/token-pairs/v1/solana/TokenA"):
            return [
                {
                    "chainId": "solana",
                    "pairAddress": "PairA2",
                    "baseToken": {"address": "TokenA", "symbol": "AAA", "name": "Alpha", "decimals": 9},
                    "quoteToken": {"address": "USDC", "symbol": "USDC", "name": "USD Coin"},
                    "liquidity": {"usd": 3500},
                    "fdv": 8000,
                }
            ]
        if url.endswith("/dex/chart/amm/v3/solana/PairA2"):
            return {
                "bars": [
                    {"timestamp": 1710000000, "open": 1.0, "high": 1.2, "low": 0.9, "close": 1.1, "volume": 100.0},
                    {"timestamp": 1710000900, "o": 1.1, "h": 1.3, "l": 1.0, "c": 1.25, "v": 130.0},
                ]
            }
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(provider, "_get_json", fake_get_json)
    records = asyncio.run(provider.get_token_history(session=None, address="TokenA", days=1))

    assert len(records) == 2
    assert records[0][1] == "TokenA"
    assert records[0][2:7] == (1.0, 1.2, 0.9, 1.1, 100.0)
    assert records[0][7] == 3500.0
    assert records[0][8] == 8000.0
    assert records[0][9] == "dexscreener"
