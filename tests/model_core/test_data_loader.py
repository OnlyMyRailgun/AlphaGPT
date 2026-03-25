import importlib
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def reload_module(module_name: str):
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def build_ohlcv_frame():
    return pd.DataFrame(
        [
            {"time": "2026-03-20 00:00:00", "address": "A", "open": 1.0, "high": 1.1, "low": 0.9, "close": 1.05, "volume": 100.0, "liquidity": 1000.0, "fdv": 5000.0},
            {"time": "2026-03-20 00:15:00", "address": "A", "open": 1.05, "high": 1.15, "low": 1.0, "close": 1.1, "volume": 120.0, "liquidity": 1000.0, "fdv": 5000.0},
            {"time": "2026-03-20 00:00:00", "address": "B", "open": 2.0, "high": 2.2, "low": 1.8, "close": 2.1, "volume": 200.0, "liquidity": 2000.0, "fdv": 7000.0},
            {"time": "2026-03-20 00:15:00", "address": "B", "open": 2.1, "high": 2.25, "low": 2.0, "close": 2.2, "volume": 220.0, "liquidity": 2000.0, "fdv": 7000.0},
        ]
    )


def test_load_data_filters_single_source(monkeypatch):
    data_loader_module = reload_module("model_core.data_loader")
    read_queries = []

    def fake_create_engine(_):
        return object()

    def fake_read_sql(query, engine):
        read_queries.append(query)
        if "SELECT address FROM tokens" in query:
            return pd.DataFrame({"address": ["A", "B"]})
        return build_ohlcv_frame()

    monkeypatch.setattr(data_loader_module.sqlalchemy, "create_engine", fake_create_engine)
    monkeypatch.setattr(data_loader_module.pd, "read_sql", fake_read_sql)

    loader = data_loader_module.CryptoDataLoader()
    loader.load_data(limit_tokens=10, source="birdeye")

    assert "source = 'birdeye'" in read_queries[0]
    assert "source = 'birdeye'" in read_queries[1]


def test_load_data_filters_multiple_sources(monkeypatch):
    data_loader_module = reload_module("model_core.data_loader")
    read_queries = []

    def fake_create_engine(_):
        return object()

    def fake_read_sql(query, engine):
        read_queries.append(query)
        if "SELECT address FROM tokens" in query:
            return pd.DataFrame({"address": ["A", "B"]})
        return build_ohlcv_frame()

    monkeypatch.setattr(data_loader_module.sqlalchemy, "create_engine", fake_create_engine)
    monkeypatch.setattr(data_loader_module.pd, "read_sql", fake_read_sql)

    loader = data_loader_module.CryptoDataLoader()
    loader.load_data(limit_tokens=10, source=["birdeye", "tushare"])

    assert "source IN ('birdeye', 'tushare')" in read_queries[0]
    assert "source IN ('birdeye', 'tushare')" in read_queries[1]


def test_load_data_keeps_default_behavior_without_source(monkeypatch):
    data_loader_module = reload_module("model_core.data_loader")
    read_queries = []

    def fake_create_engine(_):
        return object()

    def fake_read_sql(query, engine):
        read_queries.append(query)
        if "SELECT address FROM tokens" in query:
            return pd.DataFrame({"address": ["A", "B"]})
        return build_ohlcv_frame()

    monkeypatch.setattr(data_loader_module.sqlalchemy, "create_engine", fake_create_engine)
    monkeypatch.setattr(data_loader_module.pd, "read_sql", fake_read_sql)

    loader = data_loader_module.CryptoDataLoader()
    loader.load_data(limit_tokens=10)

    assert "source =" not in read_queries[0]
    assert "source IN" not in read_queries[0]
    assert "source =" not in read_queries[1]
    assert "source IN" not in read_queries[1]
