from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WIFISENSE_", env_file=".env", extra="ignore")
    mode: Literal["simulation", "system"] = "simulation"
    database_url: str | None = None
    interface: str = ""

    @property
    def database(self) -> str:
        return self.database_url or f"sqlite:///./wifisense-{self.mode}.db"
