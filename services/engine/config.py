from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    MODE: str = "paper"  # paper | live
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""
    BINANCE_TESTNET: bool = False

    DEEPSEEK_API_KEY: str = ""

    MIN_NOTIONAL_USD: float = 1.0
    MAX_POSITION_USD: float = 500.0
    DAILY_LOSS_LIMIT_USD: float = 50.0
    PAPER_STARTING_USDT: float = 10000.0

    ENGINE_HOST: str = "0.0.0.0"
    ENGINE_PORT: int = 8787
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_live(self) -> bool:
        return self.MODE.lower() == "live"

@lru_cache
def get_settings() -> Settings:
    return Settings()
