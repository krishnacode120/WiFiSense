import math
import time
from app.adapters.base_wifi_adapter import WifiAdapter, WifiError
from app.schemas import Network


class SimulatedWifiAdapter(WifiAdapter):
    def __init__(self):
        self.current: str | None = None
        self.online = True
        self.oscillate = True
        self.networks = [
            Network(ssid="Home_5G", bssid="02:00:00:00:00:01", signal_strength=96, rssi=-42, security="WPA2-Personal", band="5 GHz", channel=36),
            Network(ssid="Home_2G", bssid="02:00:00:00:00:02", signal_strength=78, rssi=-61, security="WPA2-Personal", band="2.4 GHz", channel=6),
            Network(ssid="OfficeWiFi", bssid="02:00:00:00:00:03", signal_strength=86, rssi=-54, security="WPA3-Personal", band="5 GHz", channel=44),
            Network(ssid="CafeGuest", bssid="02:00:00:00:00:04", signal_strength=46, rssi=-77, security="Open", band="2.4 GHz", channel=11),
        ]

    def scan_networks(self):
        drift = round(math.sin(time.monotonic() / 18) * 3) if self.oscillate else 0
        return [n.model_copy(update={"signal_strength": max(0, min(100, n.signal_strength + drift)), "connected": n.bssid == self.current}) for n in self.networks]

    def get_current_network(self):
        return next((n for n in self.scan_networks() if n.connected), None)

    def connect(self, network, password):
        match = next((n for n in self.networks if n.ssid == network.ssid and n.bssid == network.bssid), None)
        if not match:
            raise WifiError("Network disappeared; scan again")
        if match.security != "Open" and not password:
            raise WifiError("A user-provided credential is required")
        self.current = match.bssid

    def disconnect(self):
        self.current = None
