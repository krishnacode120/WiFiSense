import ctypes
from unittest.mock import MagicMock
from xml.etree import ElementTree as ET
import pytest
from app.adapters.windows_wifi_adapter import WindowsWifiAdapter, parse_scan, parse_interfaces, security_type
from app.adapters.windows_wlan import profile_xml, WlanSession, Parameters, Guid, U32
from app.adapters.base_wifi_adapter import WifiError
from app.schemas import Network

SCAN = """
Interface name : Wi-Fi
There are 2 networks currently visible.
SSID 1 : Home_5G
    Network type : Infrastructure
    Authentication : WPA2-Personal
    Encryption : CCMP
    BSSID 1 : 02:00:00:00:00:01
         Signal : 92%
         Band : 5 GHz
         Channel : 36
SSID 2 : CafeGuest
    Authentication : Open
    BSSID 1 : 02:00:00:00:00:04
         Signal : 44%
         Channel : 11
"""
INTERFACE = """
    Name : Wi-Fi
    Description : Synthetic adapter
    GUID : 01234567-89ab-cdef-0123-456789abcdef
    State : connected
    SSID : Home_5G
    BSSID : 02:00:00:00:00:01
    Authentication : WPA2-Personal
    Signal : 92%
    Channel : 36
    Band : 5 GHz
"""


def test_windows_parses_scan_without_fabricating_rssi():
    networks = parse_scan(SCAN)
    assert len(networks) == 2
    assert networks[0].ssid == "Home_5G"
    assert networks[0].signal_strength == 92
    assert networks[0].rssi is None
    assert networks[0].channel == 36
    assert networks[1].security == "Open"


def test_windows_scan_and_current_are_same_interface(monkeypatch):
    adapter = WindowsWifiAdapter()
    monkeypatch.setattr(adapter, "_run", lambda *args: SCAN if "networks" in args else INTERFACE)
    assert adapter.get_current_network().ssid == "Home_5G"
    assert adapter.scan_networks()[0].connected


def test_multiple_interfaces_require_selection(monkeypatch):
    adapter = WindowsWifiAdapter()
    monkeypatch.setattr(adapter, "_run", lambda *args: INTERFACE + INTERFACE.replace("Wi-Fi", "Wi-Fi 2"))
    with pytest.raises(WifiError, match="Multiple"):
        adapter.get_current_network()


def test_missing_or_localized_interface_fails_closed(monkeypatch):
    adapter = WindowsWifiAdapter()
    monkeypatch.setattr(adapter, "_run", lambda *args: "No wireless interface")
    with pytest.raises(WifiError):
        adapter.scan_networks()


def test_xml_escapes_secret_and_ssid():
    network = Network(ssid='Home<&', signal_strength=80, security="WPA2-Personal")
    xml = profile_xml(network, "synthetic<&pass")
    root = ET.fromstring(xml)
    ns = {"w": "http://www.microsoft.com/networking/WLAN/profile/v1"}
    assert root.find("w:connectionMode", ns).text == "manual"
    assert root.find(".//w:keyMaterial", ns).text == "synthetic<&pass"
    assert root.find(".//w:hex", ns).text == network.ssid.encode().hex()
    assert "synthetic<&pass" not in xml


def test_open_profile_has_no_secret():
    xml = profile_xml(Network(ssid="Cafe", signal_strength=10, security="Open"), None)
    assert "sharedKey" not in xml


def test_native_bridge_uses_temporary_profile_and_bssid(monkeypatch):
    seen = {}
    api = MagicMock()
    def open_handle(version, reserved, negotiated, handle):
        ctypes.cast(handle, ctypes.POINTER(ctypes.c_void_p))[0] = ctypes.c_void_p(123)
        return 0
    def connect(handle, guid, parameters, reserved):
        p = ctypes.cast(parameters, ctypes.POINTER(Parameters)).contents
        seen.update(mode=p.mode, xml=p.profile, bssid=bytes(p.bssids.contents.address))
        return 0
    api.WlanOpenHandle.side_effect = open_handle
    api.WlanConnect.side_effect = connect
    monkeypatch.setattr(ctypes, "WinDLL", lambda name: api, raising=False)
    with WlanSession("01234567-89ab-cdef-0123-456789abcdef") as session:
        session.connect(Network(ssid="Home", bssid="02:00:00:00:00:01", signal_strength=80, security="WPA2-Personal"), "synthetic-pass")
    assert seen["mode"] == 1
    assert seen["bssid"] == bytes.fromhex("020000000001")
    assert "synthetic-pass" in seen["xml"]
    api.WlanCloseHandle.assert_called_once()


def test_enterprise_cannot_be_mislabeled_personal():
    assert security_type("WPA2-Enterprise") == "Enterprise (unsupported)"
