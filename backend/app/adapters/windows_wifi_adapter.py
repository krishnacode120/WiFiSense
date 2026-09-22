import os
import re
import subprocess
import sys
import time
from app.adapters.base_wifi_adapter import WifiAdapter, WifiError
from app.adapters.windows_wlan import WlanSession
from app.schemas import Network


def security_type(value):
    text = value.lower()
    if "enterprise" in text or "802.1x" in text:
        return "Enterprise (unsupported)"
    if "wpa3" in text:
        return "WPA3-Personal"
    if "wpa2" in text and ("personal" in text or "psk" in text):
        return "WPA2-Personal"
    if text == "open":
        return "Open"
    return "Unsupported"


def parse_interfaces(output):
    interfaces = []
    current = None
    for line in output.splitlines():
        if ":" not in line:
            continue
        key, value = [p.strip() for p in line.split(":", 1)]
        if key == "Name":
            current = {}
            interfaces.append(current)
        if current is not None:
            current[key] = value
    return interfaces


def parse_scan(output):
    networks, ssid, security, item = [], "", "Unsupported", None
    for line in output.splitlines():
        match = re.match(r"\s*SSID\s+\d+\s*:\s?(.*)", line)
        if match:
            ssid, security, item = match[1].strip(), "Unsupported", None
            continue
        if ":" not in line:
            continue
        key, value = [p.strip() for p in line.split(":", 1)]
        if key == "Authentication":
            security = security_type(value)
        elif re.fullmatch(r"BSSID\s+\d+", key):
            if not re.fullmatch(r"(?:[a-fA-F0-9]{2}:){5}[a-fA-F0-9]{2}", value):
                continue
            item = Network(ssid=ssid, bssid=value.lower(), signal_strength=0, security=security)
            networks.append(item)
        elif item:
            if key == "Signal" and re.fullmatch(r"\d+%", value):
                item.signal_strength = min(100, int(value[:-1]))
            elif key == "Channel" and value.isdigit():
                item.channel = int(value)
            elif key == "Band":
                item.band = value
    for n in networks:
        if not n.band and n.channel:
            n.band = "2.4 GHz (inferred)" if n.channel <= 14 else "5 GHz (inferred)"
    return networks


class WindowsWifiAdapter(WifiAdapter):
    def __init__(self, interface=""):
        self.interface = interface

    def _run(self, *args):
        executable = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "netsh.exe")
        try:
            result = subprocess.run([executable, *args], capture_output=True, timeout=10, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except (OSError, subprocess.TimeoutExpired):
            raise WifiError("Windows Wi-Fi command is unavailable or timed out") from None
        if result.returncode:
            raise WifiError("Windows Wi-Fi operation failed; check radio, location permission and WLAN service")
        return result.stdout.decode("oem" if sys.platform == "win32" else "utf-8", errors="replace")

    def _interface(self):
        interfaces = parse_interfaces(self._run("wlan", "show", "interfaces"))
        if not interfaces:
            raise WifiError("No readable Wi-Fi interface; enable WLAN and use an English Windows display language")
        if self.interface:
            chosen = next((i for i in interfaces if i["Name"] == self.interface), None)
            if not chosen:
                raise WifiError("Configured Windows Wi-Fi interface was not found")
        elif len(interfaces) != 1:
            raise WifiError("Multiple Wi-Fi interfaces; set WIFISENSE_INTERFACE explicitly")
        else:
            chosen = interfaces[0]
        if "GUID" not in chosen or "State" not in chosen:
            raise WifiError("Windows interface information is incomplete")
        return chosen

    def scan_networks(self):
        interface = self._interface()
        output = self._run("wlan", "show", "networks", "mode=bssid", "interface=" + interface["Name"])
        if "SSID" not in output:
            raise WifiError("Wi-Fi scan unavailable; check radio and Windows location permissions")
        networks = parse_scan(output)
        current = self.get_current_network()
        for n in networks:
            n.connected = bool(current and n.bssid == current.bssid and n.ssid == current.ssid)
        return networks

    def get_current_network(self):
        data = self._interface()
        if data["State"] != "connected":
            return None
        signal = re.search(r"\d+", data.get("Signal", "0"))
        channel = data.get("Channel", "")
        bssid = data.get("AP BSSID") or data.get("BSSID")
        return Network(ssid=data.get("SSID", ""), bssid=bssid.lower() if bssid else None,
                       signal_strength=min(100, int(signal[0])) if signal else 0,
                       security=security_type(data.get("Authentication", "")),
                       channel=int(channel) if channel.isdigit() else None, band=data.get("Band"), connected=True)

    def connect(self, network, password):
        interface = self._interface()
        with WlanSession(interface["GUID"]) as session:
            session.connect(network, password)
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            current = self.get_current_network()
            if current and current.ssid == network.ssid and current.security == network.security and (not network.bssid or current.bssid == network.bssid):
                return
            time.sleep(.5)
        self.disconnect()
        raise WifiError("Windows connection timed out; verify passphrase and network availability")

    def disconnect(self):
        interface = self._interface()
        with WlanSession(interface["GUID"]) as session:
            session.disconnect()

    def gateway(self):
        interface = self._interface()
        output = self._run("interface", "ipv4", "show", "config", "name=" + interface["Name"])
        match = re.search(r"Default Gateway:\s*(\d+\.\d+\.\d+\.\d+)", output)
        return match[1] if match else None
