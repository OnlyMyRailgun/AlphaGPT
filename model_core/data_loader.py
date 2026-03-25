import pandas as pd
import torch
import sqlalchemy
from .config import ModelConfig
from .factors import FeatureEngineer

class CryptoDataLoader:
    def __init__(self):
        self.engine = sqlalchemy.create_engine(ModelConfig.DB_URL)
        self.feat_tensor = None
        self.raw_data_cache = None
        self.target_ret = None

    def _normalize_sources(self, source):
        if source is None:
            return None
        if isinstance(source, str):
            sources = [source]
        else:
            sources = list(source)
        normalized = [item.strip() for item in sources if item and item.strip()]
        return normalized or None

    def _build_source_filter(self, source, table_alias=""):
        sources = self._normalize_sources(source)
        if not sources:
            return ""

        prefix = f"{table_alias}." if table_alias else ""
        quoted = ", ".join(f"'{item}'" for item in sources)
        if len(sources) == 1:
            return f" AND {prefix}source = '{sources[0]}'"
        return f" AND {prefix}source IN ({quoted})"

    def load_data(self, limit_tokens=500, source=None):
        print("Loading data from SQL...")
        source_filter = self._build_source_filter(source)
        top_query = f"""
        SELECT DISTINCT o.address FROM tokens t
        JOIN ohlcv o ON o.address = t.address
        WHERE 1=1{source_filter.replace('source', 'o.source')}
        LIMIT {limit_tokens} 
        """
        addrs = pd.read_sql(top_query, self.engine)['address'].tolist()
        if not addrs:
            raise ValueError("No tokens found.")
        addr_str = "'" + "','".join(addrs) + "'"
        data_query = f"""
        SELECT time, address, open, high, low, close, volume, liquidity, fdv
        FROM ohlcv
        WHERE address IN ({addr_str})
        {source_filter}
        ORDER BY time ASC
        """
        df = pd.read_sql(data_query, self.engine)

        def to_tensor(col):
            pivot = df.pivot(index='time', columns='address', values=col)
            pivot = pivot.ffill().fillna(0.0)
            return torch.tensor(pivot.values.T, dtype=torch.float32, device=ModelConfig.DEVICE)

        self.raw_data_cache = {
            'open': to_tensor('open'),
            'high': to_tensor('high'),
            'low': to_tensor('low'),
            'close': to_tensor('close'),
            'volume': to_tensor('volume'),
            'liquidity': to_tensor('liquidity'),
            'fdv': to_tensor('fdv')
        }
        self.feat_tensor = FeatureEngineer.compute_features(self.raw_data_cache)
        op = self.raw_data_cache['open']
        t1 = torch.roll(op, -1, dims=1)
        t2 = torch.roll(op, -2, dims=1)
        self.target_ret = torch.log(t2 / (t1 + 1e-9))
        self.target_ret[:, -2:] = 0.0
        print(f"Data Ready. Shape: {self.feat_tensor.shape}")
