import math
import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator

Security = Literal["WPA2-Personal", "WPA3-Personal", "Open"]


class Network(BaseModel):
    ssid: str
    bssid: str | None = None
    signal_strength: int = Field(ge=0, le=100)
    rssi: int | None = None
    security: str
    band: str | None = None
    channel: int | None = None
    connected: bool = False
    trusted: bool = False
    trusted_id: str | None = None
    quality: str = "Unknown"
    score: float | None = None


class TrustCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ssid: str
    bssid: str = ""
    security: Security
    password: SecretStr | None = None
    authorized: Literal[True]
    auto_connect_enabled: bool = True
    priority: int = Field(default=0, ge=-10, le=10)

    @field_validator("ssid")
    @classmethod
    def valid_ssid(cls, value):
        if not 1 <= len(value.encode("utf-8")) <= 32 or any(ord(c) < 32 or ord(c) == 127 for c in value):
            raise ValueError("SSID must be 1–32 UTF-8 bytes without control characters")
        return value

    @field_validator("bssid")
    @classmethod
    def valid_bssid(cls, value):
        if value and not re.fullmatch(r"(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", value):
            raise ValueError("Invalid BSSID")
        return value.lower()

    @model_validator(mode="after")
    def credential_required(self):
        if self.security != "Open":
            password = self.password.get_secret_value() if self.password else ""
            if not 8 <= len(password) <= 63 or any(ord(c) < 32 or ord(c) == 127 for c in password):
                raise ValueError("Personal Wi-Fi passphrase must contain 8–63 characters without controls")
        elif self.password:
            raise ValueError("Open networks do not take a password")
        return self


class TrustUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    auto_connect_enabled: bool | None = None
    priority: int | None = Field(default=None, ge=-10, le=10)


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    auto_connect: bool = False
    smart_roaming: bool = True
    scan_interval: int = Field(default=10, ge=5, le=300)
    monitoring_interval: int = Field(default=5, ge=5, le=300)
    history_interval: int = Field(default=30, ge=10, le=3600)
    minimum_signal: int = Field(default=25, ge=0, le=100)
    switch_threshold: float = Field(default=15, ge=1, le=100)
    sustain_seconds: int = Field(default=15, ge=10, le=120)
    roaming_cooldown: int = Field(default=60, ge=10, le=3600)
    preferred_network: str | None = None
    weights: dict[str, float] = Field(default_factory=lambda: {"signal": .55, "connectivity": .20, "latency": .15, "stability": .10})

    @field_validator("weights")
    @classmethod
    def normalize(cls, value):
        if set(value) != {"signal", "connectivity", "latency", "stability"}:
            raise ValueError("All four ranking weights are required")
        if any(not math.isfinite(v) or v < 0 for v in value.values()) or sum(value.values()) <= 0:
            raise ValueError("Weights must be finite, non-negative, with a positive sum")
        total = sum(value.values())
        return {k: v / total for k, v in value.items()}
