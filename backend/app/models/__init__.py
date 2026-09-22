from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class TrustedNetwork(Base):
    __tablename__ = "trusted_networks"
    __table_args__ = (UniqueConstraint("ssid", "bssid", "mode"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    ssid: Mapped[str] = mapped_column(String(32))
    bssid: Mapped[str] = mapped_column(String(17), default="")
    security: Mapped[str] = mapped_column(String)
    mode: Mapped[str] = mapped_column(String)
    auto_connect_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NetworkHistory(Base):
    __tablename__ = "network_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    ssid: Mapped[str] = mapped_column(String)
    bssid: Mapped[str | None] = mapped_column(String, nullable=True)
    mode: Mapped[str] = mapped_column(String)
    signal_strength: Mapped[int] = mapped_column(Integer)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    internet_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    dns_working: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class SignalHistory(Base):
    __tablename__ = "signal_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    ssid: Mapped[str] = mapped_column(String)
    mode: Mapped[str] = mapped_column(String)
    signal_strength: Mapped[int] = mapped_column(Integer)
    rssi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class ConnectionEvent(Base):
    __tablename__ = "connection_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    ssid: Mapped[str | None] = mapped_column(String, nullable=True)
    mode: Mapped[str] = mapped_column(String)
    event: Mapped[str] = mapped_column(String)
    detail: Mapped[str] = mapped_column(String, default="")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)
