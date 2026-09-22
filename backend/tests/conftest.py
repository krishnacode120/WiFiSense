import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Config
from app.adapters.simulated_wifi_adapter import SimulatedWifiAdapter


@pytest.fixture
def client(tmp_path):
    adapter = SimulatedWifiAdapter()
    adapter.oscillate = False
    app = create_app(Config(mode="simulation", database_url=f"sqlite:///{tmp_path / 'test.db'}"), adapter=adapter, monitor=False)
    with TestClient(app, headers={"X-WiFiSense": "local-dashboard"}) as client:
        yield client


@pytest.fixture
def manager(client):
    return client.app.state.manager


def trust(client, ssid="Home_5G", **kw):
    return client.post("/api/wifi/trusted", json={"ssid": ssid, "security": "WPA2-Personal", "password": "simulation-only-passphrase", "authorized": True, **kw})
