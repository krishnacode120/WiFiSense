"""Minimal native WLAN bridge: credentials stay in an in-memory temporary profile."""
import ctypes as C
import uuid
from xml.etree import ElementTree as ET
from app.adapters.base_wifi_adapter import WifiError

U32 = C.c_uint32


class Guid(C.Structure):
    _fields_ = [("bytes", C.c_ubyte * 16)]


class Header(C.Structure):
    _fields_ = [("type", C.c_ubyte), ("revision", C.c_ubyte), ("size", C.c_uint16)]


class BssidList(C.Structure):
    _fields_ = [("header", Header), ("count", U32), ("total", U32), ("address", C.c_ubyte * 6)]


class Parameters(C.Structure):
    _fields_ = [("mode", C.c_int), ("profile", C.c_wchar_p), ("ssid", C.c_void_p),
                ("bssids", C.POINTER(BssidList)), ("bss_type", C.c_int), ("flags", U32)]


def profile_xml(network, password):
    auth = {"WPA2-Personal": "WPA2PSK", "WPA3-Personal": "WPA3SAE", "Open": "open"}.get(network.security)
    if not auth:
        raise WifiError("Windows adapter supports Open, WPA2-Personal and WPA3-Personal only")
    if auth != "open" and not password:
        raise WifiError("An explicit user-provided passphrase is required")
    root = ET.Element("WLANProfile", xmlns="http://www.microsoft.com/networking/WLAN/profile/v1")
    ET.SubElement(root, "name").text = "WiFiSense-temporary"
    config = ET.SubElement(root, "SSIDConfig")
    ssid = ET.SubElement(config, "SSID")
    ET.SubElement(ssid, "hex").text = network.ssid.encode("utf-8").hex()
    ET.SubElement(root, "connectionType").text = "ESS"
    ET.SubElement(root, "connectionMode").text = "manual"
    security = ET.SubElement(ET.SubElement(root, "MSM"), "security")
    encryption = ET.SubElement(security, "authEncryption")
    ET.SubElement(encryption, "authentication").text = auth
    ET.SubElement(encryption, "encryption").text = "none" if auth == "open" else "AES"
    ET.SubElement(encryption, "useOneX").text = "false"
    if auth != "open":
        key = ET.SubElement(security, "sharedKey")
        ET.SubElement(key, "keyType").text = "passPhrase"
        ET.SubElement(key, "protected").text = "false"
        ET.SubElement(key, "keyMaterial").text = password
    return ET.tostring(root, encoding="unicode")


class WlanSession:
    def __init__(self, guid):
        self.guid = Guid((C.c_ubyte * 16).from_buffer_copy(uuid.UUID(guid.strip("{}")).bytes_le))
        self.handle = C.c_void_p()
        self.api = C.WinDLL("wlanapi.dll")  # instantiated only on Windows
        self.api.WlanOpenHandle.argtypes = [U32, C.c_void_p, C.POINTER(U32), C.POINTER(C.c_void_p)]
        self.api.WlanOpenHandle.restype = U32
        self.api.WlanCloseHandle.argtypes = [C.c_void_p, C.c_void_p]
        self.api.WlanCloseHandle.restype = U32
        self.api.WlanConnect.argtypes = [C.c_void_p, C.POINTER(Guid), C.POINTER(Parameters), C.c_void_p]
        self.api.WlanConnect.restype = U32
        self.api.WlanDisconnect.argtypes = [C.c_void_p, C.POINTER(Guid), C.c_void_p]
        self.api.WlanDisconnect.restype = U32

    def __enter__(self):
        negotiated = U32()
        if self.api.WlanOpenHandle(2, None, C.byref(negotiated), C.byref(self.handle)):
            raise WifiError("Windows WLAN service is unavailable or access is denied")
        return self

    def __exit__(self, *args):
        self.api.WlanCloseHandle(self.handle, None)

    def connect(self, network, password):
        buffer = C.create_unicode_buffer(profile_xml(network, password))
        desired = None
        if network.bssid:
            desired = BssidList(Header(0x80, 1, C.sizeof(BssidList)), 1, 1,
                                (C.c_ubyte * 6).from_buffer_copy(bytes.fromhex(network.bssid.replace(":", ""))))
        parameters = Parameters(1, C.cast(buffer, C.c_wchar_p), None,
                                C.pointer(desired) if desired else None, 1, 0)
        try:
            # mode=1 means temporary XML profile, never a saved profile/file.
            result = self.api.WlanConnect(self.handle, C.byref(self.guid), C.byref(parameters), None)
            if result:
                raise WifiError("Windows rejected the connection request; verify security and permissions")
        finally:
            C.memset(C.addressof(buffer), 0, C.sizeof(buffer))

    def disconnect(self):
        if self.api.WlanDisconnect(self.handle, C.byref(self.guid), None):
            raise WifiError("Windows could not disconnect this Wi-Fi interface")
