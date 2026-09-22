import subprocess
from types import SimpleNamespace
import pytest
from app.adapters.linux_wifi_adapter import LinuxWifiAdapter, parse_scan, split_escaped
from app.adapters.base_wifi_adapter import WifiError
from app.schemas import Network

SCAN = r"*:" + r"Lab\:West:02\:00\:00\:00\:00\:01:90:WPA2:36:5180 MHz" + "\n" + r":Cafe:02\:00\:00\:00\:00\:04:40:--:11:2462 MHz"


def test_nmcli_escaped_ssid_and_bssid():
    networks = parse_scan(SCAN)
    assert len(networks) == 2
    assert networks[0].ssid == "Lab:West"
    assert networks[0].bssid == "02:00:00:00:00:01"
    assert networks[0].connected and networks[0].band == "5 GHz"
    assert networks[0].rssi is None
    assert networks[1].security == "Open"


def test_secret_only_on_stdin_and_profile_never_persisted(monkeypatch):
    calls = []
    adapter = LinuxWifiAdapter("wlan0")
    monkeypatch.setattr(adapter, "_interface", lambda: "wlan0")
    target = Network(ssid='Lab:West', bssid="02:00:00:00:00:01", signal_strength=90, security="WPA2-Personal")
    monkeypatch.setattr(adapter, "get_current_network", lambda: target)
    def run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout="")
    monkeypatch.setattr(subprocess, "run", run)
    adapter.connect(target, "synthetic<&pass")
    assert all("synthetic<&pass" not in str(args) for args, kwargs in calls)
    assert any(kwargs.get("input") == "802-11-wireless-security.psk:synthetic<&pass\n" for args, kwargs in calls)
    creation = calls[0][0]
    assert creation[creation.index("save") + 1] == "no"
    assert creation[creation.index("connection.autoconnect") + 1] == "no"
    assert creation[creation.index("wifi-sec.psk-flags") + 1] == "2"
    assert calls[1][0][-2:] == ["passwd-file", "/dev/stdin"]
    assert all(not kwargs.get("shell") for args, kwargs in calls)


def test_disabled_wifi(monkeypatch):
    adapter = LinuxWifiAdapter()
    monkeypatch.setattr(adapter, "_run", lambda *args: "disabled")
    with pytest.raises(WifiError, match="disabled"):
        adapter.scan_networks()


def test_runner_redacts_stderr(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *args, **kw: SimpleNamespace(returncode=10, stdout="", stderr="secret-value"))
    with pytest.raises(WifiError) as error:
        LinuxWifiAdapter()._run("radio", "wifi")
    assert "secret-value" not in str(error.value)


def test_failed_activation_removes_own_profile(monkeypatch):
    adapter = LinuxWifiAdapter()
    monkeypatch.setattr(adapter, "_interface", lambda: "wlan0")
    calls = []
    def run(*args, **kw):
        calls.append(args)
        if "up" in args:
            raise WifiError("Activation failed")
        return ""
    monkeypatch.setattr(adapter, "_run", run)
    with pytest.raises(WifiError):
        adapter.connect(Network(ssid="Cafe", signal_strength=80, security="Open"), None)
    assert calls[-1][:3] == ("connection", "delete", "uuid")
    assert not adapter.owned_profiles
