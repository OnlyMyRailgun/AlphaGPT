from abc import ABC, abstractmethod

class DataProvider(ABC):
    provider_name: str = ""
    session_headers: dict[str, str]

    @abstractmethod
    async def get_trending_tokens(self, limit: int):
        pass

    @abstractmethod
    async def get_token_history(self, session, address: str, days: int):
        pass
