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


def load_run_pipeline(monkeypatch, data_provider, api_key=""):
    monkeypatch.setenv("DATA_PROVIDER", data_provider)
    monkeypatch.setenv("BIRDEYE_API_KEY", api_key)
    reload_module("data_pipeline.config")
    reload_module("data_pipeline.providers.birdeye")
    reload_module("data_pipeline.providers.dexscreener")
    reload_module("data_pipeline.data_manager")
    return reload_module("data_pipeline.run_pipeline")


def test_run_pipeline_only_requires_birdeye_key_in_birdeye_mode(monkeypatch):
    run_pipeline = load_run_pipeline(monkeypatch, "dexscreener", "")
    asyncio.run(run_pipeline.main())

    run_pipeline = load_run_pipeline(monkeypatch, "birdeye", "")
    asyncio.run(run_pipeline.main())


def test_pipeline_uses_selected_provider(monkeypatch):
    data_manager_module = load_run_pipeline(monkeypatch, "dexscreener", "").DataManager
    manager = data_manager_module()
    assert manager.provider.provider_name == "dexscreener"
