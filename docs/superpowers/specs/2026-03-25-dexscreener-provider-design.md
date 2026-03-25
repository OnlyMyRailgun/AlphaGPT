# DexScreener Provider Switch Design

## Summary

Add explicit environment-based data provider selection to the crypto data pipeline so the repository can run with either Birdeye or DexScreener. The selected provider is controlled by `DATA_PROVIDER=birdeye|dexscreener`.

## Goals

- Support both Birdeye and DexScreener behind the same pipeline entrypoint.
- Use environment configuration to choose the active provider.
- Keep downstream storage and model code unchanged by normalizing provider output.
- Require `BIRDEYE_API_KEY` only when `DATA_PROVIDER=birdeye`.

## Non-Goals

- No automatic fallback between providers.
- No support for providers beyond Birdeye and DexScreener in this change.
- No schema changes outside fields already written into `tokens` and `ohlcv`.

## Current State

- `run_pipeline.py` always requires `BIRDEYE_API_KEY`.
- `DataManager` instantiates both providers directly and always uses Birdeye for candidate discovery and OHLCV fetching.
- `DexScreenerProvider` only partially exists: batch token details is implemented, while trending discovery and historical fetch return empty lists.
- There is no automated test suite in the repository yet for the data pipeline.

## Proposed Design

### Configuration

Add `DATA_PROVIDER` to `data_pipeline/config.py` with valid values `birdeye` and `dexscreener`. Normalize input to lowercase and validate eagerly.

Rules:

- `DATA_PROVIDER=birdeye` requires a non-empty `BIRDEYE_API_KEY`.
- `DATA_PROVIDER=dexscreener` does not require an API key.
- Existing `BIRDEYE_API_KEY` remains unchanged.
- Existing `USE_DEXSCREENER` becomes obsolete and is removed.

### Provider Interface

Expand the provider abstraction so both providers expose a consistent surface:

- `provider_name`
- `session_headers`
- `get_trending_tokens(limit)`
- `get_token_details_batch(session, addresses)`
- `get_token_history(session, address, days)`

Returned token dictionaries must contain:

- `address`
- `symbol`
- `name`
- `decimals`
- `liquidity`
- `fdv`

Returned OHLCV records must match the existing insert format:

- `(time, address, open, high, low, close, volume, liquidity, fdv, source)`

### Provider Selection

`DataManager` will select exactly one provider during initialization based on `Config.DATA_PROVIDER`. The rest of the pipeline uses `self.provider` only.

### DexScreener Discovery

DexScreener does not offer the same “trending token” endpoint shape as Birdeye in this codebase, so discovery will be implemented as a two-step flow:

1. Fetch Solana token candidates from the public DexScreener token listing endpoint already implied by the current provider.
2. Normalize and deduplicate by token address, choosing the highest-liquidity pair per token.

If the initial discovery endpoint yields incomplete token metadata, `get_token_details_batch()` is used to enrich the candidate list before filtering and storage.

### DexScreener OHLCV

Implement historical candle fetch using DexScreener’s public chart/candle endpoint for Solana pairs or tokens, then normalize each candle into the repository’s existing OHLCV tuple format. When liquidity and FDV are unavailable at candle granularity, use `0.0` to preserve the current schema contract.

### Error Handling

- Invalid `DATA_PROVIDER` raises a clear configuration error.
- Birdeye mode without API key fails fast before pipeline startup.
- Provider HTTP errors return empty results with provider-specific logging.
- Rate limiting uses bounded retry behavior where already present; no unbounded recursion is introduced.

## Testing Strategy

Add pytest-based tests covering:

1. Config/provider validation
2. DataManager provider selection
3. DexScreener token normalization
4. DexScreener candle normalization
5. Pipeline behavior that only Birdeye mode requires API key

Tests should avoid real network access by using fake sessions and monkeypatched responses.

## Risks

- DexScreener’s public endpoints may not expose metadata identical to Birdeye; normalization must handle missing fields safely.
- Discovery quality may differ across providers, so pipeline output may not be identical between modes.
- Existing code imports `Config` statically, so tests should patch module attributes carefully or reload modules when validating config branches.

## Acceptance Criteria

- `uv run python -m data_pipeline.run_pipeline` works in `birdeye` mode when `BIRDEYE_API_KEY` is set.
- `uv run python -m data_pipeline.run_pipeline` works in `dexscreener` mode without `BIRDEYE_API_KEY`.
- `DataManager.pipeline_sync_daily()` uses the selected provider only.
- README and `.env.example` document the new switch clearly.
