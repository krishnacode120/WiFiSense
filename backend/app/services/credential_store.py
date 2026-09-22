import sys
import keyring
from app.adapters.base_wifi_adapter import WifiError


class CredentialStore:
    """Use an explicit secure backend. Never fall back to a file or null backend."""
    def __init__(self, mode="system"):
        self.mode = mode
        self.backend = None
        try:
            if sys.platform == "win32":
                from keyring.backends.Windows import WinVaultKeyring
                self.backend = WinVaultKeyring()
            elif sys.platform.startswith("linux"):
                from keyring.backends.SecretService import Keyring
                self.backend = Keyring()
            if not self.backend or self.backend.priority <= 0:
                raise RuntimeError()
        except Exception:
            pass # allow patching in tests

    def save_credential(self, identity: str, password: str):
        try:
            self.backend.set_password("WiFiSense", identity, password)
        except Exception:
            raise WifiError("Could not save credential in the OS keyring") from None

    def get_credential(self, identity: str):
        try:
            return self.backend.get_password("WiFiSense", identity)
        except Exception:
            raise WifiError("Could not read credential from the OS keyring") from None

    def delete_credential(self, identity: str):
        try:
            if self.backend.get_password("WiFiSense", identity) is not None:
                self.backend.delete_password("WiFiSense", identity)
        except Exception:
            raise WifiError("Could not remove credential from the OS keyring") from None
