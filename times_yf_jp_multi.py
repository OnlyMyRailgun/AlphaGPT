import json
import random
from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import times_yf_jp as experiment

N_RUNS = 5
OUTPUT_PATH = Path("times_yf_jp_runs.json")


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def compute_metrics(test_ret, strategy_equity):
    ann_ret = strategy_equity[-1] ** (252 / len(strategy_equity)) - 1
    vol = np.std(test_ret) * np.sqrt(252)
    sharpe = (ann_ret - 0.02) / (vol + 1e-6)
    dd = 1 - strategy_equity / np.maximum.accumulate(strategy_equity)
    max_dd = np.max(dd)
    calmar = ann_ret / (max_dd + 1e-6)
    return {
        "total_return": float(strategy_equity[-1] - 1),
        "ann_return": float(ann_ret),
        "ann_volatility": float(vol),
        "sharpe": float(sharpe),
        "max_drawdown": float(max_dd),
        "calmar": float(calmar),
    }


def evaluate_run(miner, engine):
    factor_all = miner.solve_one(miner.best_formula_tokens)
    split = engine.split_idx
    test_factors = factor_all[split:].cpu().numpy()
    test_ret = engine.target_oto_ret[split:].cpu().numpy()

    signal = np.tanh(test_factors)
    position = np.sign(signal)
    turnover = np.abs(position - np.roll(position, 1))
    turnover[0] = 0
    strategy_ret = position * test_ret - turnover * experiment.COST_RATE
    strategy_equity = (1 + strategy_ret).cumprod()
    bench_equity = (1 + test_ret).cumprod()

    return {
        "strategy": compute_metrics(strategy_ret, strategy_equity),
        "buy_hold": compute_metrics(test_ret, bench_equity),
    }


def write_summary(output_path: Path, runs: list[dict]) -> None:
    best_run = max(runs, key=lambda item: item["strategy"]["sharpe"])
    payload = {
        "n_runs": len(runs),
        "best_run": best_run,
        "runs": runs,
    }
    output_path.write_text(json.dumps(payload, indent=2))


def run_experiment(n_runs: int = N_RUNS, output_path: Path = OUTPUT_PATH):
    engine = experiment.DataEngine()
    engine.load()
    runs = []

    for run_id in range(1, n_runs + 1):
        seed = random.randint(1, 10_000_000)
        set_seed(seed)
        miner = experiment.DeepQuantMiner(engine)
        miner.train()
        metrics = evaluate_run(miner, engine)
        run = {
            "run_id": run_id,
            "seed": seed,
            "formula_tokens": miner.best_formula_tokens,
            "formula": miner.decode(),
            **metrics,
        }
        runs.append(run)
        print(
            f"[Run {run_id}/{n_runs}] Sharpe={run['strategy']['sharpe']:.2f} "
            f"AnnRet={run['strategy']['ann_return']:.2%} Formula={run['formula']}"
        )

    write_summary(output_path, runs)
    best_run = max(runs, key=lambda item: item["strategy"]["sharpe"])
    print(f"\nSaved summary to {output_path}")
    print(
        f"Best run #{best_run['run_id']} | Sharpe={best_run['strategy']['sharpe']:.2f} "
        f"| AnnRet={best_run['strategy']['ann_return']:.2%}"
    )
    print(f"Best formula: {best_run['formula']}")


if __name__ == "__main__":
    run_experiment()
