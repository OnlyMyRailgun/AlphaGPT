import importlib.util
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def load_module():
    path = ROOT / "times_yf_jp.py"
    spec = importlib.util.spec_from_file_location("times_yf_jp", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_times_yf_jp_loads_mock_yfinance_data(monkeypatch, tmp_path):
    module = load_module()
    module.DATA_CACHE_PATH = str(tmp_path / "yf_jp_cache.parquet")

    dates = pd.date_range("2024-01-01", periods=8, freq="D")
    frame = pd.DataFrame(
        {
            "Open": [1, 2, 3, 4, 5, 6, 7, 8],
            "High": [2, 3, 4, 5, 6, 7, 8, 9],
            "Low": [0.5, 1, 2, 3, 4, 5, 6, 7],
            "Close": [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5],
            "Volume": [10, 12, 14, 16, 18, 20, 22, 24],
        },
        index=dates,
    )

    monkeypatch.setattr(module.yf, "download", lambda *args, **kwargs: frame)

    engine = module.DataEngine()
    engine.load()

    assert module.INDEX_CODE == "1570.T"
    assert engine.feat_data.shape[0] == 5
    assert engine.raw_open.shape[0] == len(frame)
