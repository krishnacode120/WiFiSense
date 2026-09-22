from concurrent.futures import ThreadPoolExecutor
import ipaddress
import math
from app.adapters.base_wifi_adapter import WifiError
import socket
import subprocess
import sys
import time
import dns.resolver


class ConnectivityTest:
    """One gateway echo, one TCP handshake, one bounded DNS lookup; no scanning."""
    def __init__(self, adapter, simulation=False):
        self.adapter, self.simulation = adapter, simulation

    def run(self):
        if self.simulation:
            online = self.adapter.online
            return {"internet_available": online, "latency_ms": round(18 + 5 * abs(math.sin(time.monotonic() / 10)), 1) if online else None,
                    "dns_working": online, "gateway_reachable": True, "packet_loss_percent": None, "probe": "simulation"}
        def gateway():
            try:
                address = self.adapter.gateway()
                if not address:
                    return None
                address = str(ipaddress.ip_address(address))
                args = ["ping", "-n", "1", "-w", "1000", address] if sys.platform == "win32" else ["ping", "-c", "1", "-W", "1", address]
                return subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2).returncode == 0
            except (ValueError, OSError, subprocess.TimeoutExpired, WifiError):
                return None
        def internet():
            start = time.monotonic()
            try:
                with socket.create_connection(("1.1.1.1", 443), timeout=2):
                    return True, round((time.monotonic() - start) * 1000, 1)
            except OSError:
                return False, None
        def check_dns():
            try:
                dns.resolver.resolve("example.com", "A", lifetime=2)
                return True
            except Exception:
                return False
        with ThreadPoolExecutor(max_workers=3) as pool:
            gw, tcp, resolution = pool.submit(gateway), pool.submit(internet), pool.submit(check_dns)
            available, latency = tcp.result()
            return {"gateway_reachable": gw.result(), "internet_available": available, "latency_ms": latency,
                    "dns_working": resolution.result(), "packet_loss_percent": None, "probe": "TCP handshake to 1.1.1.1:443"}

