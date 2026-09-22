from abc import ABC, abstractmethod
from app.schemas import Network


class WifiError(Exception):
    """Only fixed, user-safe messages; never wrap raw subprocess output."""


class WifiAdapter(ABC):
    @abstractmethod
    def scan_networks(self) -> list[Network]: ...

    @abstractmethod
    def get_current_network(self) -> Network | None: ...

    @abstractmethod
    def connect(self, network: Network, password: str | None) -> None: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    def get_signal_strength(self) -> int | None:
        current = self.get_current_network()
        return current.signal_strength if current else None

    def gateway(self) -> str | None:
        return None
