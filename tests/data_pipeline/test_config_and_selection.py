import importlib
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def reload_module(module_name: str):
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def load_modules(monkeypatch, data_provider, api_key=""):
    monkeypatch.setenv("DATA_PROVIDER", data_provider)
    monkeypatch.setenv("BIRDEYE_API_KEY", api_key)
    config_module = reload_module("data_pipeline.config")
    provider_birdeye = reload_module("data_pipeline.providers.birdeye")
    provider_dexscreener = reload_module("data_pipeline.providers.dexscreener")
    data_manager_module = reload_module("data_pipeline.data_manager")
    return config_module, data_manager_module, provider_birdeye, provider_dexscreener


def test_invalid_data_provider_raises(monkeypatch):
    monkeypatch.setenv("DATA_PROVIDER", "unknown")
    monkeypatch.setenv("BIRDEYE_API_KEY", "")
    with pytest.raises(ValueError, match="Invalid DATA_PROVIDER"):
        reload_module("data_pipeline.config")


def test_birdeye_requires_api_key(monkeypatch):
    config_module, _, _, _ = load_modules(monkeypatch, "birdeye", "")
    with pytest.raises(ValueError, match="BIRDEYE_API_KEY is required"):
        config_module.Config.validate_runtime()


def test_dexscreener_does_not_require_api_key(monkeypatch):
    config_module, _, _, _ = load_modules(monkeypatch, "dexscreener", "")
    config_module.Config.validate_runtime()


def test_data_manager_selects_dexscreener_provider(monkeypatch):
    _, data_manager_module, _, _ = load_modules(monkeypatch, "dexscreener", "")
    manager = data_manager_module.DataManager()
    assert manager.provider.provider_name == "dexscreener"
