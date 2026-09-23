import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Config
from fakes import FakeWifiAdapter, FakeCredentialStore, FakeConnectivity


@pytest.fixture
def client(tmp_path):
    adapter = FakeWifiAdapter()
    adapter.oscillate = False
    app = create_app(
        Config(mode="system", database_url=f"sqlite:///{tmp_path / 'test.db'}"),
        adapter=adapter, credential_store=FakeCredentialStore(),
        connectivity=FakeConnectivity(adapter), monitor=False,
    )
    with TestClient(app, headers={"X-WiFiSense": "local-dashboard"}) as client:
        yield client


@pytest.fixture
def manager(client):
    return client.app.state.manager


def trust(client, ssid="Home_5G", **kw):
    return client.post("/api/wifi/trusted", json={"ssid": ssid, "security": "WPA2-Personal", "password": "test-only-passphrase", "authorized": True, **kw})
