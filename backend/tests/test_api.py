import pytest
from conftest import trust


@pytest.mark.parametrize("payload", [
    {"authorized": False}, {"ssid": ""}, {"ssid": "a" * 33}, {"ssid": "evil\nSSID"},
    {"bssid": "invalid"}, {"password": "short"}, {"priority": 11}, {"password": {"sensitive": "data"}}
])
def test_validation_redacts_all_inputs(client, payload):
    result = trust(client, **payload)
    assert result.status_code == 422
    assert "short" not in result.text
    assert "simulation-only-passphrase" not in result.text
    assert "sensitive" not in result.text
    assert "input" not in result.text


def test_authorization_required(client):
    result = client.post("/api/wifi/trusted", json={"ssid": "CafeGuest", "security": "Open"})
    assert result.status_code == 422


def test_csrf_and_host_protection(client):
    assert client.post("/api/wifi/disconnect", headers={"X-WiFiSense": ""}).status_code == 403
    assert client.post("/api/wifi/disconnect", headers={"Origin": "https://evil.test"}).status_code == 403
    assert client.get("/api/wifi/scan", headers={"Host": "evil.test"}).status_code == 400
    assert client.options("/api/wifi/trusted", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "x-wifisense"}).status_code == 200


def test_settings_validation_and_persistence(client, manager):
    original = client.get("/api/settings").json()
    invalid = {**original, "scan_interval": 1}
    assert client.put("/api/settings", json=invalid).status_code == 422
    preferred = {**original, "preferred_network": "untrusted"}
    assert client.put("/api/settings", json=preferred).status_code == 409
    updated = {**original, "scan_interval": 20, "weights": {"signal": 4, "connectivity": 3, "latency": 2, "stability": 1}}
    result = client.put("/api/settings", json=updated)
    assert result.status_code == 200
    assert result.json()["weights"]["signal"] == .4
    from app.models import Setting
    with manager.sessions() as db:
        assert db.get(Setting, "system").value["scan_interval"] == 20


def test_pagination_and_openapi(client):
    assert client.get("/api/wifi/history?limit=0").status_code == 422
    assert client.get("/api/wifi/history?offset=-1").status_code == 422
    spec = client.get("/openapi.json").json()
    assert len(spec["paths"]) >= 12


def test_duplicate_and_update(client):
    n = trust(client).json()
    assert trust(client).status_code == 409
    response = client.patch("/api/wifi/trusted/" + n["id"], json={"priority": 4, "auto_connect_enabled": False})
    assert response.status_code == 200
    assert response.json()["priority"] == 4
    assert response.json()["auto_connect_enabled"] is False
