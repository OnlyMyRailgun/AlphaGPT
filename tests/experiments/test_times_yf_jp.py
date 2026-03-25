import importlib.util
from pathlib import Path

import pandas as pd
import torch


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


def test_times_yf_jp_backtest_matches_reference_logic():
    module = load_module()

    class DummyEngine:
        split_idx = 6
        target_oto_ret = torch.tensor([0.01, -0.02, 0.03, 0.01, -0.01, 0.02, 0.0], dtype=torch.float32)

    miner = module.DeepQuantMiner.__new__(module.DeepQuantMiner)
    miner.engine = DummyEngine()

    factors = torch.tensor(
        [
            [0.5, 0.3, -0.2, 0.6, 0.1, 0.2, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [-0.3, -0.2, -0.1, 0.4, 0.5, 0.6, 0.0],
        ],
        dtype=torch.float32,
    )

    def reference_backtest(factors_tensor):
        rewards = torch.zeros(factors_tensor.shape[0], device=module.DEVICE)
        target = miner.engine.target_oto_ret[: miner.engine.split_idx]
        for i in range(factors_tensor.shape[0]):
            factor = factors_tensor[i, : miner.engine.split_idx]
            if torch.isnan(factor).all() or (factor == 0).all() or factor.numel() == 0:
                rewards[i] = -2.0
                continue

            sig = torch.tanh(factor)
            pos = torch.sign(sig)
            turnover = torch.abs(pos - torch.roll(pos, 1))
            if turnover.numel() > 0:
                turnover[0] = 0.0
            else:
                rewards[i] = -2.0
                continue

            pnl = pos * target - turnover * module.COST_RATE
            if pnl.numel() < 10:
                rewards[i] = -2.0
                continue

            mu = pnl.mean()
            std = pnl.std() + 1e-6
            downside_returns = pnl[pnl < 0]
            if downside_returns.numel() > 5:
                down_std = downside_returns.std() + 1e-6
                sortino = mu / down_std * 15.87
            else:
                sortino = mu / std * 15.87

            if mu < 0:
                sortino = -2.0
            if turnover.mean() > 0.5:
                sortino -= 1.0
            if (pos == 0).all():
                sortino = -2.0

            rewards[i] = sortino
        return torch.clamp(rewards, -3, 5)

    expected = reference_backtest(factors)
    actual = module.DeepQuantMiner.backtest(miner, factors)
    torch.testing.assert_close(actual, expected)
