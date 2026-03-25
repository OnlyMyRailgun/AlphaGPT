import os
from dotenv import load_dotenv

load_dotenv()


def _parse_data_provider(raw_value: str) -> str:
    provider = (raw_value or "birdeye").strip().lower()
    valid_providers = {"birdeye", "dexscreener"}
    if provider not in valid_providers:
        raise ValueError(
            f"Invalid DATA_PROVIDER '{raw_value}'. Expected one of: {sorted(valid_providers)}"
        )
    return provider

class Config:
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "crypto_quant")
    DB_DSN = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    CHAIN = "solana"
    TIMEFRAME = "15m" # 也支持 15min
    MIN_LIQUIDITY_USD = 500000.0  
    MIN_FDV = 1000000.0            
    MAX_FDV = float('inf') 
    DATA_PROVIDER = _parse_data_provider(os.getenv("DATA_PROVIDER", "birdeye"))
    BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY", "")
    BIRDEYE_IS_PAID = False
    BIRDEYE_RPS = float(os.getenv("BIRDEYE_RPS", "1"))
    BIRDEYE_RETRY_LIMIT = int(os.getenv("BIRDEYE_RETRY_LIMIT", "3"))
    CONCURRENCY = 1
    HISTORY_DAYS = int(os.getenv("HISTORY_DAYS", "30"))
    DEXSCREENER_API_BASE = os.getenv("DEXSCREENER_API_BASE", "https://api.dexscreener.com")
    DEXSCREENER_CHART_API_URL = os.getenv(
        "DEXSCREENER_CHART_API_URL",
        "https://io.dexscreener.com/dex/chart/amm/v3"
    )

    @classmethod
    def validate_runtime(cls):
        if cls.DATA_PROVIDER == "birdeye" and not cls.BIRDEYE_API_KEY:
            raise ValueError("BIRDEYE_API_KEY is required when DATA_PROVIDER=birdeye")
