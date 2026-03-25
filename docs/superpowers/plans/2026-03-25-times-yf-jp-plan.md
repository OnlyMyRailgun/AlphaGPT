# times_yf_jp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a standalone `times_yf_jp.py` experiment script that trains on `1570.T` using `yfinance`.

**Architecture:** Copy the existing `times.py` experiment shape, replace the Tushare data fetch with `yfinance`, keep the training loop intact, and add a small smoke test around the new data loader.

**Tech Stack:** Python, yfinance, pandas, torch, pytest

---

### Task 1: Add a failing smoke test

**Files:**
- Create: `tests/experiments/test_times_yf_jp.py`

- [ ] **Step 1: Write the failing test**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement the minimal script to satisfy the loader contract**
- [ ] **Step 4: Run test to verify it passes**

### Task 2: Create the standalone yfinance experiment

**Files:**
- Create: `times_yf_jp.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Copy and adapt the experiment script**
- [ ] **Step 2: Add `yfinance` dependency**
- [ ] **Step 3: Verify script imports and starts**

### Task 3: Verify and document run commands

**Files:**
- Modify: none

- [ ] **Step 1: Run focused tests**
- [ ] **Step 2: Verify `py_compile`**
- [ ] **Step 3: Provide local and Colab run commands**
