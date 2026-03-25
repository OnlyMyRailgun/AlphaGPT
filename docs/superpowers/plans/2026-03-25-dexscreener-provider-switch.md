# DexScreener Provider Switch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `DATA_PROVIDER=birdeye|dexscreener` so the data pipeline can run against either provider through the same code path.

**Architecture:** Introduce explicit provider selection in config, route `DataManager` through a single provider abstraction, and normalize DexScreener token/history responses into the existing storage format. Keep the rest of the pipeline and database schema unchanged.

**Tech Stack:** Python 3.11, aiohttp, asyncpg, pytest

---

### Task 1: Add test scaffolding for config and provider selection

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/data_pipeline/test_config_and_selection.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write the failing tests**

```python
def test_invalid_data_provider_raises():
    ...

def test_birdeye_requires_api_key():
    ...

def test_data_manager_selects_dexscreener_provider():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/data_pipeline/test_config_and_selection.py -v`
Expected: FAIL because pytest is not configured and provider selection helpers do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add pytest dependency, implement config parsing helpers, and update `DataManager` to select one provider based on `Config.DATA_PROVIDER`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/data_pipeline/test_config_and_selection.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml tests/conftest.py tests/data_pipeline/test_config_and_selection.py data_pipeline/config.py data_pipeline/data_manager.py
git commit -m "test: cover provider config and selection"
```

### Task 2: Add failing tests for DexScreener normalization

**Files:**
- Create: `tests/data_pipeline/test_dexscreener_provider.py`
- Modify: `data_pipeline/providers/base.py`
- Modify: `data_pipeline/providers/dexscreener.py`

- [ ] **Step 1: Write the failing tests**

```python
async def test_get_trending_tokens_normalizes_highest_liquidity_pair():
    ...

async def test_get_token_history_normalizes_candles():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/data_pipeline/test_dexscreener_provider.py -v`
Expected: FAIL because DexScreener methods still return empty lists or lack shared interface fields.

- [ ] **Step 3: Write minimal implementation**

Expand the provider base contract, implement DexScreener discovery/history methods, and normalize missing fields safely.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/data_pipeline/test_dexscreener_provider.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/data_pipeline/test_dexscreener_provider.py data_pipeline/providers/base.py data_pipeline/providers/dexscreener.py
git commit -m "feat: implement dexscreener provider normalization"
```

### Task 3: Route the pipeline through the selected provider

**Files:**
- Modify: `data_pipeline/data_manager.py`
- Modify: `data_pipeline/run_pipeline.py`
- Create: `tests/data_pipeline/test_run_pipeline.py`

- [ ] **Step 1: Write the failing tests**

```python
async def test_pipeline_uses_selected_provider():
    ...

def test_run_pipeline_only_requires_birdeye_key_in_birdeye_mode():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/data_pipeline/test_run_pipeline.py -v`
Expected: FAIL because the pipeline still hardcodes Birdeye and always enforces the key check.

- [ ] **Step 3: Write minimal implementation**

Use `self.provider` for candidate discovery, session headers, and history fetches. Update startup validation and logging to reflect the configured provider.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/data_pipeline/test_run_pipeline.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/data_pipeline/test_run_pipeline.py data_pipeline/data_manager.py data_pipeline/run_pipeline.py
git commit -m "feat: route pipeline through selected provider"
```

### Task 4: Document the new provider switch

**Files:**
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `CATREADME.md`

- [ ] **Step 1: Write the failing doc expectations**

Document expected examples for:
- `DATA_PROVIDER=birdeye`
- `DATA_PROVIDER=dexscreener`
- Birdeye key requirement only in Birdeye mode

- [ ] **Step 2: Verify docs are currently incomplete**

Run: `rg -n "DATA_PROVIDER|dexscreener" README.md CATREADME.md .env.example`
Expected: missing or incomplete coverage

- [ ] **Step 3: Write minimal documentation updates**

Add environment examples and explain provider selection behavior.

- [ ] **Step 4: Verify docs are updated**

Run: `rg -n "DATA_PROVIDER|dexscreener|BIRDEYE_API_KEY" README.md CATREADME.md .env.example`
Expected: all relevant docs mention the new switch clearly

- [ ] **Step 5: Commit**

```bash
git add .env.example README.md CATREADME.md
git commit -m "docs: document provider selection"
```

### Task 5: Run the focused verification suite

**Files:**
- Modify: none

- [ ] **Step 1: Run focused tests**

Run: `uv run pytest tests/data_pipeline -v`
Expected: PASS

- [ ] **Step 2: Run a lightweight static verification**

Run: `uv run python -m compileall data_pipeline tests`
Expected: PASS

- [ ] **Step 3: Summarize any residual risk**

Note that live network behavior still depends on third-party API availability and may require follow-up integration testing with real credentials/endpoints.
