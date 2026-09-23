import pytest
from pydantic import ValidationError
from app.schemas import Settings, TrustCreate
from app.services.signal_analyzer import get_signal_quality
from app.services.network_ranker import score_network
from app.services.roaming_manager import RoamingManager
from app.services.credential_store import CredentialStore
from app.adapters.base_wifi_adapter import WifiError
from conftest import trust


@pytest.mark.parametrize("rssi,rating", [(-30,"Excellent"),(-50,"Excellent"),(-51,"Very Good"),(-60,"Very Good"),(-61,"Good"),(-67,"Good"),(-68,"Fair"),(-75,"Fair"),(-76,"Weak"),(-110,"Weak")])
def test_signal_ranges(rssi, rating):
    result = get_signal_quality(rssi)
    assert result["rating"] == rating
    assert 0 <= result["quality"] <= 100


def test_example_conversion():
    assert get_signal_quality(-58)["quality"] == 82


def test_scoring_all_components_and_priority():
    s = Settings()
    assert score_network(80, {"internet_available": True, "latency_ms": 40}, 90, 0, False, s) == 85
    assert score_network(80, None, 50, 0, False, s) == 66.5
    assert score_network(80, None, 50, 10, True, s) == 81.5


def test_weights_normalize():
    assert sum(Settings(weights=dict(signal=55, connectivity=20, latency=15, stability=10)).weights.values()) == 1
    for weights in [dict(signal=0, connectivity=0, latency=0, stability=0), dict(signal=-1, connectivity=1, latency=1, stability=1), {"signal": 1}]:
        with pytest.raises(ValidationError):
            Settings(weights=weights)


def test_roaming_hysteresis_cooldown_and_reset():
    r, s = RoamingManager(), Settings()
    assert not r.should_switch("a", 90, 60, 0, s)
    assert not r.should_switch("a", 90, 60, 14, s)
    assert r.should_switch("a", 90, 60, 15, s)
    r.switched(15)
    assert not r.should_switch("b", 100, 40, 30, s)
    assert not r.should_switch("b", 100, 40, 76, s)
    assert not r.should_switch("b", 50, 40, 80, s)
    assert not r.should_switch("b", 100, 40, 90, s)
    assert r.should_switch("b", 100, 40, 105, s)


def test_credential_interface():
    class MockBackend:
        def __init__(self):
            self.memory = {}
        def set_password(self, service, identity, password):
            self.memory[identity] = password
        def get_password(self, service, identity):
            return self.memory.get(identity)
        def delete_password(self, service, identity):
            self.memory.pop(identity, None)
            
    store = object.__new__(CredentialStore)
    store.backend = MockBackend()
    store.save_credential("ssid-id", "not-a-real-credential")
    assert store.get_credential("ssid-id") == "not-a-real-credential"
    store.delete_credential("ssid-id")
    assert store.get_credential("ssid-id") is None


def test_credential_backend_failure_is_redacted():
    class Broken:
        def get_password(self, *args):
            raise RuntimeError("sensitive value from backend")
    store = object.__new__(CredentialStore)
    store.backend = Broken()
    with pytest.raises(WifiError, match="Could not read") as exc:
        store.get_credential("id")
    assert "sensitive" not in str(exc.value)


def test_initial_state_requires_explicit_trust(client, manager):
    assert len(client.get("/api/wifi/scan").json()) == 4
    assert client.get("/api/wifi/trusted").json() == []
    client.post("/api/wifi/auto-connect/enable")
    manager.tick()
    assert manager.adapter.current is None
    assert client.post("/api/wifi/connect/unknown").status_code == 409


def test_signal_not_enough_without_trust(client, manager):
    home = trust(client, "Home_2G").json()
    client.post("/api/wifi/auto-connect/enable")
    manager.tick()
    assert manager.current.ssid == "Home_2G"
    assert manager.current.trusted_id is None  # adapter objects carry no DB authorization
    assert client.get("/api/wifi/current").json()["network"]["trusted_id"] == home["id"]


def test_network_ranking_prefers_quality(client, manager):
    trust(client)
    trust(client, "Home_2G")
    trusted = [n for n in manager.scan() if n.trusted]
    assert [n.ssid for n in trusted] == ["Home_5G", "Home_2G"]
    assert trusted[0].score > trusted[1].score


def test_do_not_reconnect_and_manual_disconnect_pauses(client, manager, monkeypatch):
    home = trust(client).json()
    client.post("/api/wifi/connect/" + home["id"])
    calls = []
    monkeypatch.setattr(manager.adapter, "connect", lambda *args: calls.append(args))
    client.post("/api/wifi/auto-connect/enable")
    manager.tick()
    assert calls == []
    assert client.post("/api/wifi/disconnect").json()["auto_connect"] is False
    manager.tick()
    assert manager.current is None


def test_bssid_and_security_are_enforced(client, manager):
    home = trust(client, bssid="02:00:00:00:00:ff").json()
    assert not any(n.trusted for n in manager.scan())
    assert client.post("/api/wifi/connect/" + home["id"]).status_code == 409
    client.delete("/api/wifi/trusted/" + home["id"])
    home = trust(client).json()
    manager.adapter.networks[0].security = "Open"
    assert client.post("/api/wifi/connect/" + home["id"]).status_code == 409


def test_disabled_trusted_is_never_automatic(client, manager):
    home = trust(client, auto_connect_enabled=False).json()
    client.post("/api/wifi/auto-connect/enable")
    manager.tick()
    assert manager.current is None
    assert client.post("/api/wifi/connect/" + home["id"]).status_code == 200


def test_failed_connection_backoff_and_no_secret(client, manager, monkeypatch):
    home = trust(client).json()
    calls = []
    def broken(*args):
        calls.append(True)
        raise RuntimeError("test-only-passphrase")
    monkeypatch.setattr(manager.adapter, "connect", broken)
    result = client.post("/api/wifi/connect/" + home["id"])
    assert result.status_code == 409
    assert "test-only-passphrase" not in result.text
    client.post("/api/wifi/auto-connect/enable")
    manager.tick()
    assert len(calls) == 1


def test_internet_events_and_metrics(client, manager):
    home = trust(client).json()
    assert client.post("/api/wifi/connect/" + home["id"]).status_code == 200
    manager.adapter.online = False
    manager.tick()
    manager.adapter.online = True
    manager.tick()
    events = [e["event"] for e in client.get("/api/wifi/history").json()]
    assert {"connected", "internet_lost", "internet_restored"} <= set(events)
    data = client.get("/api/wifi/metrics").json()
    assert data["connections"][0]["ssid"] == "Home_5G"
    assert data["connections"][0]["internet_available"] is True


def test_disappearing_network(client, manager):
    home = trust(client).json()
    manager.adapter.networks = []
    assert client.post("/api/wifi/connect/" + home["id"]).status_code == 409


def test_untrusted_current_is_not_probed(client, manager, monkeypatch):
    manager.adapter.current = manager.adapter.networks[2].bssid
    calls = []
    monkeypatch.setattr(manager.connectivity, "run", lambda: calls.append(True))
    manager.tick()
    assert calls == []


def test_password_not_in_db_logs_or_api(client, manager, capsys):
    result = trust(client)
    assert result.status_code == 201
    identity = result.json()["id"]
    assert "password" not in result.text
    client.post("/api/wifi/connect/" + identity)
    for endpoint in ("/wifi/trusted", "/wifi/current", "/wifi/scan", "/wifi/history", "/wifi/metrics", "/system/status"):
        text = client.get("/api" + endpoint).text
        assert "test-only-passphrase" not in text
    with manager.sessions() as db:
        from sqlalchemy import text
        script = "\n".join(db.connection().connection.driver_connection.iterdump())
        assert "test-only-passphrase" not in script
        assert "password" not in script.lower()
    assert "test-only-passphrase" not in capsys.readouterr().err
    assert client.delete("/api/wifi/trusted/" + identity).status_code == 200
    assert manager.credentials.get_credential(identity) is None

def test_missing_credential_does_not_starve_other_trusted_networks(client, manager):
    home = trust(client).json()
    trust(client, "Home_2G")
    manager.credentials.delete_credential(home["id"])
    client.post("/api/wifi/auto-connect/enable")
    with pytest.raises(WifiError, match="Credential"):
        manager.tick()
    manager.tick()
    assert manager.current.ssid == "Home_2G"


def test_sustained_roaming_integration(client, manager):
    import time
    trust(client)
    slower = trust(client, "Home_2G").json()
    client.post("/api/wifi/connect/" + slower["id"])
    manager.adapter.networks[1].signal_strength = 20
    manager.adapter.networks[1].rssi = -90
    manager.scanner.last_scan = float("-inf")
    manager.roaming.last_switch = float("-inf")
    client.post("/api/wifi/auto-connect/enable")
    manager.tick()
    assert manager.current.ssid == "Home_2G"
    manager.roaming.since = time.monotonic() - 16
    manager.tick()
    assert manager.current.ssid == "Home_5G"
    assert "switched" in [e["event"] for e in client.get("/api/wifi/history").json()]





def test_monitor_history_is_rate_limited(client, manager):
    trust(client)
    manager.tick()
    first = len(client.get("/api/wifi/metrics").json()["signals"])
    manager.tick()
    assert len(client.get("/api/wifi/metrics").json()["signals"]) == first
