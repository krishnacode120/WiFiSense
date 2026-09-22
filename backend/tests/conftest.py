import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Config
from app.adapters.simulated_wifi_adapter import SimulatedWifiAdapter


@pytest.fixture
def client(tmp_path):
    adapter = SimulatedWifiAdapter()
    adapter.oscillate = False
    
    class MockCredentialStore:
        def __init__(self):
            self.memory = {}
        def save_credential(self, identity, password):
            self.memory[identity] = password
        def get_credential(self, identity):
            return self.memory.get(identity)
        def delete_credential(self, identity):
            self.memory.pop(identity, None)
            
    app = create_app(Config(mode="system", database_url=f"sqlite:///{tmp_path / 'test.db'}"), adapter=adapter, credential_store=MockCredentialStore(), monitor=False)
    with TestClient(app, headers={"X-WiFiSense": "local-dashboard"}) as client:
        # mock connectivity test to prevent actual pings in tests
        client.app.state.manager.connectivity = type("MockConnectivity", (), {"run": lambda self: {"internet_available": client.app.state.manager.adapter.online, "latency_ms": 20, "dns_working": True, "gateway_reachable": True, "packet_loss_percent": None, "probe": "mock"}})()
        yield client


@pytest.fixture
def manager(client):
    return client.app.state.manager


def trust(client, ssid="Home_5G", **kw):
    return client.post("/api/wifi/trusted", json={"ssid": ssid, "security": "WPA2-Personal", "password": "simulation-only-passphrase", "authorized": True, **kw})
