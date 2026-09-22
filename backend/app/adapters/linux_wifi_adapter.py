import os
import subprocess
import time
import uuid
from app.adapters.base_wifi_adapter import WifiAdapter, WifiError
from app.schemas import Network


def split_escaped(line):
    fields, value, escaped = [], "", False
    for char in line:
        if escaped:
            value += char
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == ":":
            fields.append(value)
            value = ""
        else:
            value += char
    fields.append(value)
    return fields


def security_type(value):
    if "802.1X" in value or "EAP" in value:
        return "Enterprise (unsupported)"
    if "WPA3" in value:
        return "WPA3-Personal"
    if "WPA2" in value:
        return "WPA2-Personal"
    if value in {"", "--"}:
        return "Open"
    return "Unsupported"


def parse_scan(output):
    networks = []
    for line in output.splitlines():
        fields = split_escaped(line)
        if len(fields) != 7:
            continue
        active, ssid, bssid, signal, security, channel, frequency = fields
        if not signal.isdigit():
            continue
        freq = int(frequency.split()[0]) if frequency.split() and frequency.split()[0].isdigit() else 0
        networks.append(Network(ssid=ssid, bssid=bssid.lower() or None, signal_strength=min(100, int(signal)),
                                security=security_type(security), channel=int(channel) if channel.isdigit() else None,
                                band="6 GHz" if freq >= 5925 else "5 GHz" if freq >= 4900 else "2.4 GHz" if freq else None,
                                connected=active == "*"))
    return networks


class LinuxWifiAdapter(WifiAdapter):
    def __init__(self, interface=""):
        self.interface = interface
        self.owned_profiles = set()

    def _run(self, *args, input_text=None, timeout=12):
        try:
            result = subprocess.run(["nmcli", *args], input=input_text, capture_output=True, text=True,
                                    encoding="utf-8", timeout=timeout, env={**os.environ, "LC_ALL": "C"})
        except (OSError, subprocess.TimeoutExpired):
            raise WifiError("NetworkManager is unavailable or the operation timed out") from None
        if result.returncode:
            raise WifiError("NetworkManager rejected the operation; check permissions, radio state and passphrase")
        return result.stdout

    def _interface(self):
        if self._run("radio", "wifi").strip() != "enabled":
            raise WifiError("Wi-Fi is disabled; enable the radio in system settings")
        devices = [split_escaped(line) for line in self._run("-t", "-f", "DEVICE,TYPE", "device", "status").splitlines()]
        interfaces = [d[0] for d in devices if len(d) == 2 and d[1] == "wifi"]
        if self.interface:
            if self.interface not in interfaces:
                raise WifiError("Configured Wi-Fi interface was not found")
            return self.interface
        if len(interfaces) != 1:
            raise WifiError("No unique Wi-Fi adapter; set WIFISENSE_INTERFACE when multiple adapters exist")
        return interfaces[0]

    def _scan(self, rescan):
        interface = self._interface()
        output = self._run("-t", "--escape", "yes", "-f", "IN-USE,SSID,BSSID,SIGNAL,SECURITY,CHAN,FREQ",
                           "device", "wifi", "list", "ifname", interface, "--rescan", rescan)
        return parse_scan(output)

    def scan_networks(self):
        return self._scan("yes")

    def get_current_network(self):
        return next((n for n in self._scan("no") if n.connected), None)

    def connect(self, network, password):
        interface = self._interface()
        if network.security not in {"Open", "WPA2-Personal", "WPA3-Personal"}:
            raise WifiError("This security type is unsupported")
        if network.security != "Open" and not password:
            raise WifiError("A user-provided passphrase is required")
        if password and ("\n" in password or "\r" in password):
            raise WifiError("Passphrase contains invalid control characters")
        identity = str(uuid.uuid4())
        args = ["connection", "add", "save", "no", "type", "wifi", "ifname", interface,
                "con-name", "WiFiSense-" + identity, "connection.uuid", identity, "ssid", network.ssid,
                "connection.autoconnect", "no"]
        if network.bssid:
            args += ["802-11-wireless.bssid", network.bssid]
        if network.security != "Open":
            args += ["wifi-sec.key-mgmt", "sae" if network.security == "WPA3-Personal" else "wpa-psk",
                     "wifi-sec.psk-flags", "2"]
        self._run(*args)
        self.owned_profiles.add(identity)
        try:
            activation = ["--wait", "25", "connection", "up", "uuid", identity, "ifname", interface]
            if password:
                activation += ["passwd-file", "/dev/stdin"]
            self._run(*activation, input_text="802-11-wireless-security.psk:" + password + "\n" if password else None, timeout=30)
            current = self.get_current_network()
            if not current or current.ssid != network.ssid or current.security != network.security or (network.bssid and current.bssid != network.bssid):
                self._run("device", "disconnect", interface)
                raise WifiError("NetworkManager did not confirm the authorized access point")
        except WifiError:
            self._remove_profile(identity)
            raise
        for old in list(self.owned_profiles - {identity}):
            self._remove_profile(old)

    def _remove_profile(self, identity):
        try:
            self._run("connection", "delete", "uuid", identity)
            self.owned_profiles.discard(identity)
        except WifiError:
            # In-memory metadata only; autoconnect is disabled and no secret was saved.
            pass

    def disconnect(self):
        self._run("device", "disconnect", self._interface())
        for identity in list(self.owned_profiles):
            self._remove_profile(identity)

    def gateway(self):
        value = self._run("-g", "IP4.GATEWAY", "device", "show", self._interface()).strip().splitlines()
        return value[0] if value else None
