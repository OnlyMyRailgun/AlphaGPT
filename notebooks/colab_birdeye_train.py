"""
Colab helper for training AlphaGPT against a cloud PostgreSQL database.

Recommended usage in Colab:

1. Upload this file or open the repo in Colab.
2. Run:

   !pip install -U pip
   !pip install torch pandas sqlalchemy psycopg2-binary tqdm loguru python-dotenv asyncpg

3. Edit the CONFIG block below with your repo path and cloud DB URL.
4. Run:

   %run /content/AlphaGPT/notebooks/colab_birdeye_train.py
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse


# --- CONFIG ---
REPO_DIR = Path("/content/AlphaGPT")
DATA_SOURCE = "birdeye"

# Option A: paste a full cloud Postgres URL here.
CLOUD_DB_URL = os.getenv("CLOUD_DB_URL", "")

# Option B: leave CLOUD_DB_URL empty and set these individually.
DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "")

def apply_db_url_to_env(db_url: str) -> None:
    parsed = urlparse(db_url)
    if parsed.scheme not in {"postgresql", "postgres"}:
        raise ValueError(f"Unsupported DB URL scheme: {parsed.scheme}")

    os.environ["DB_HOST"] = parsed.hostname or ""
    os.environ["DB_PORT"] = str(parsed.port or 5432)
    os.environ["DB_USER"] = parsed.username or ""
    os.environ["DB_PASSWORD"] = parsed.password or ""
    os.environ["DB_NAME"] = (parsed.path or "").lstrip("/")


def configure_env() -> None:
    if CLOUD_DB_URL:
        apply_db_url_to_env(CLOUD_DB_URL)
    else:
        os.environ["DB_HOST"] = DB_HOST
        os.environ["DB_PORT"] = DB_PORT
        os.environ["DB_USER"] = DB_USER
        os.environ["DB_PASSWORD"] = DB_PASSWORD
        os.environ["DB_NAME"] = DB_NAME

    missing = [name for name in ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"] if not os.getenv(name)]
    if missing:
        raise ValueError(f"Missing database settings: {missing}")


def main() -> None:
    configure_env()
    os.chdir(REPO_DIR)

    import sys

    if str(REPO_DIR) not in sys.path:
        sys.path.insert(0, str(REPO_DIR))

    from model_core.engine import AlphaEngine

    print("Starting training")
    print(f"Repo dir: {REPO_DIR}")
    print(f"DB host: {os.environ['DB_HOST']}")
    print(f"DB name: {os.environ['DB_NAME']}")
    print(f"Data source: {DATA_SOURCE}")

    engine = AlphaEngine(use_lord_regularization=True, data_source=DATA_SOURCE)
    engine.train()


if __name__ == "__main__":
    main()
