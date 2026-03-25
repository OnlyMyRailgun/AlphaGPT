import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def reload_module(module_name: str):
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def test_strategy_config_defaults_to_birdeye(monkeypatch):
    monkeypatch.delenv("STRATEGY_DATA_SOURCE", raising=False)
    config_module = reload_module("strategy_manager.config")
    assert config_module.StrategyConfig.DATA_SOURCE == "birdeye"


def test_strategy_config_reads_env(monkeypatch):
    monkeypatch.setenv("STRATEGY_DATA_SOURCE", "yfinance")
    config_module = reload_module("strategy_manager.config")
    assert config_module.StrategyConfig.DATA_SOURCE == "yfinance"


def test_runner_uses_strategy_data_source_in_code():
    runner_path = ROOT / "strategy_manager" / "runner.py"
    text = runner_path.read_text()
    assert 'self.loader.load_data(limit_tokens=300, source=self.data_source)' in text
    assert "WHERE source = '{self.data_source}'" in text
