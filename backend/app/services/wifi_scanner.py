import time
from app.services.signal_analyzer import get_signal_quality, percentage_rating


class WifiScanner:
    def __init__(self, adapter):
        self.adapter = adapter
        self.networks = []
        self.last_scan = float("-inf")

    def scan(self, interval=10, force=False):
        if force or time.monotonic() - self.last_scan >= interval:
            self.networks = self.adapter.scan_networks()
            for n in self.networks:
                n.quality = get_signal_quality(n.rssi)["rating"] if n.rssi is not None else percentage_rating(n.signal_strength) + " (estimated)"
            self.last_scan = time.monotonic()
        return [n.model_copy() for n in self.networks]
