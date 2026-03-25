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
    monkeypatch.setenv("DATA_PROVIDER", "birdeye")
    monkeypatch.setenv("BIRDEYE_API_KEY", "test-key")
    reload_module("data_pipeline.config")
    provider_module = reload_module("data_pipeline.providers.birdeye")
    return provider_module.BirdeyeProvider()


def test_get_trending_tokens_paginates_until_limit(monkeypatch):
    provider = load_provider(monkeypatch)
    calls = []

    class FakeResponse:
        def __init__(self, status, payload):
            self.status = status
            self._payload = payload

        async def json(self):
            return self._payload

    class FakeRequest:
        def __init__(self, response):
            self.response = response

        async def __aenter__(self):
            return self.response

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeSession:
        def __init__(self, headers=None):
            self.headers = headers

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def get(self, url, params=None):
            calls.append(params.copy())
            offset = params["offset"]
            limit = params["limit"]
            page = [
                {
                    "address": f"Token{offset + i}",
                    "symbol": f"T{offset + i}",
                    "name": f"Token {offset + i}",
                    "decimals": 6,
                    "liquidity": 100000 + offset + i,
                    "fdv": 200000 + offset + i,
                }
                for i in range(limit)
            ]
            if offset >= 40:
                page = page[:5]
            payload = {"data": {"tokens": page}}
            return FakeRequest(FakeResponse(200, payload))

    provider_module = reload_module("data_pipeline.providers.birdeye")
    monkeypatch.setattr(provider_module.aiohttp, "ClientSession", FakeSession)

    tokens = asyncio.run(provider.get_trending_tokens(limit=45))

    assert len(tokens) == 45
    assert calls == [
        {"sort_by": "rank", "sort_type": "asc", "offset": 0, "limit": 20},
        {"sort_by": "rank", "sort_type": "asc", "offset": 20, "limit": 20},
        {"sort_by": "rank", "sort_type": "asc", "offset": 40, "limit": 5},
    ]
    assert tokens[0]["address"] == "Token0"
    assert tokens[-1]["address"] == "Token44"


def test_get_trending_tokens_retries_429_and_throttles(monkeypatch):
    provider = load_provider(monkeypatch)
    sleep_calls = []
    call_count = {"count": 0}

    class FakeResponse:
        def __init__(self, status, payload):
            self.status = status
            self._payload = payload

        async def json(self):
            return self._payload

    class FakeRequest:
        def __init__(self, response):
            self.response = response

        async def __aenter__(self):
            return self.response

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeSession:
        def __init__(self, headers=None):
            self.headers = headers

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def get(self, url, params=None):
            call_count["count"] += 1
            if call_count["count"] == 2:
                return FakeRequest(FakeResponse(429, {}))

            payload = {
                "data": {
                    "tokens": [
                        {
                            "address": f"Token{params['offset'] + i}",
                            "symbol": f"T{params['offset'] + i}",
                            "name": f"Token {params['offset'] + i}",
                            "decimals": 6,
                            "liquidity": 100000 + i,
                            "fdv": 200000 + i,
                        }
                        for i in range(params["limit"])
                    ]
                }
            }
            return FakeRequest(FakeResponse(200, payload))

    async def fake_sleep(seconds):
        sleep_calls.append(seconds)

    provider_module = reload_module("data_pipeline.providers.birdeye")
    monkeypatch.setattr(provider_module.aiohttp, "ClientSession", FakeSession)
    monkeypatch.setattr(provider_module.asyncio, "sleep", fake_sleep)

    tokens = asyncio.run(provider.get_trending_tokens(limit=25))

    assert len(tokens) == 25
    assert call_count["count"] == 3
    assert sleep_calls == [1.0, 1.0, 1.0]


def test_get_token_history_retries_429_with_limit(monkeypatch):
    provider = load_provider(monkeypatch)
    sleep_calls = []
    call_count = {"count": 0}

    class FakeResponse:
        def __init__(self, status, payload):
            self.status = status
            self._payload = payload

        async def json(self):
            return self._payload

    class FakeRequest:
        def __init__(self, response):
            self.response = response

        async def __aenter__(self):
            return self.response

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeSession:
        def get(self, url, params=None):
            call_count["count"] += 1
            if call_count["count"] == 1:
                return FakeRequest(FakeResponse(429, {}))
            return FakeRequest(
                FakeResponse(
                    200,
                    {
                        "data": {
                            "items": [
                                {"unixTime": 1710000000, "o": 1.0, "h": 1.2, "l": 0.9, "c": 1.1, "v": 100.0},
                            ]
                        }
                    },
                )
            )

    async def fake_sleep(seconds):
        sleep_calls.append(seconds)

    provider_module = reload_module("data_pipeline.providers.birdeye")
    monkeypatch.setattr(provider_module.asyncio, "sleep", fake_sleep)

    records = asyncio.run(provider.get_token_history(FakeSession(), "TokenA", days=1))

    assert len(records) == 1
    assert call_count["count"] == 2
    assert sleep_calls == [5, 1.0, 1.0]
