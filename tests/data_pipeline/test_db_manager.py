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


def test_batch_insert_ohlcv_uses_conflict_safe_insert():
    db_module = reload_module("data_pipeline.db_manager")
    executed = []
    copied = []

    class FakeTransaction:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeConn:
        async def execute(self, sql):
            executed.append(sql.strip())

        async def copy_records_to_table(self, table, records, columns, timeout=None):
            copied.append(
                {
                    "table": table,
                    "records": list(records),
                    "columns": list(columns),
                    "timeout": timeout,
                }
            )

        def transaction(self):
            return FakeTransaction()

    class FakeAcquire:
        def __init__(self, conn):
            self.conn = conn

        async def __aenter__(self):
            return self.conn

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakePool:
        def __init__(self):
            self.conn = FakeConn()

        def acquire(self):
            return FakeAcquire(self.conn)

    mgr = db_module.DBManager()
    mgr.pool = FakePool()

    records = [
        ("2026-03-01 00:00:00", "A", 1.0, 1.1, 0.9, 1.0, 10.0, 1000.0, 5000.0, "birdeye"),
        ("2026-03-01 00:15:00", "A", 1.0, 1.1, 0.9, 1.0, 10.0, 1000.0, 5000.0, "birdeye"),
    ]

    asyncio.run(mgr.batch_insert_ohlcv(records))

    assert copied[0]["table"] == "ohlcv_staging"
    assert "CREATE TEMP TABLE ohlcv_staging" in executed[0]
    assert "INSERT INTO ohlcv" in executed[1]
    assert "ON CONFLICT (time, address, source) DO NOTHING" in executed[1]
