import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_module():
    path = ROOT / "times_yf_jp_multi.py"
    spec = importlib.util.spec_from_file_location("times_yf_jp_multi", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_multi_run_writes_summary_json(tmp_path):
    module = load_module()
    output_path = tmp_path / "runs.json"

    runs = [
        {
            "run_id": 1,
            "formula_tokens": [1, 2, 3],
            "formula": "RET5",
            "strategy": {"ann_return": 0.1, "sharpe": 0.5},
            "buy_hold": {"ann_return": 0.2, "sharpe": 0.3},
        },
        {
            "run_id": 2,
            "formula_tokens": [4, 5, 6],
            "formula": "TREND",
            "strategy": {"ann_return": 0.2, "sharpe": 0.8},
            "buy_hold": {"ann_return": 0.2, "sharpe": 0.3},
        },
    ]

    module.write_summary(output_path, runs)
    payload = json.loads(output_path.read_text())

    assert payload["best_run"]["run_id"] == 2
    assert payload["runs"][0]["formula"] == "RET5"
    assert payload["runs"][1]["strategy"]["sharpe"] == 0.8
