# times_yf_jp Design

## Summary

Create a standalone `times_yf_jp.py` experiment script by copying the current `times.py` workflow and replacing the Tushare data source with `yfinance`.

## Goal

Provide a minimal, runnable Japan ETF experiment that uses `1570.T` by default and can be executed both locally and in Colab without touching the main crypto pipeline.

## Scope

- Create a new standalone script: `times_yf_jp.py`
- Default ticker: `1570.T`
- Use `yfinance` to fetch OHLCV history
- Preserve the current training and evaluation flow from `times.py`
- Add one smoke test for data loading behavior

## Non-Goals

- No integration with `data_pipeline`
- No database writes
- No multi-ticker portfolio support
- No refactor of the existing `times.py`

## Design

The new script mirrors the structure of `times.py`, but swaps the Tushare `DataEngine` implementation for a `yfinance`-based loader. Data is downloaded once, normalized into the same feature tensors, cached to a local parquet file, and then fed into the same miner/training loop.

The script remains self-contained so that it can be run directly in Colab with a short install command and no dependency on project database configuration.
