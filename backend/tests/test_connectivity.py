from types import SimpleNamespace
from app.services.connectivity_test import ConnectivityTest


def test_safe_probes_and_unknown_packet_loss(monkeypatch):
    class Socket:
        def __enter__(self): return self
        def __exit__(self, *args): pass
    monkeypatch.setattr("socket.create_connection", lambda *args, **kw: Socket())
    monkeypatch.setattr("dns.resolver.resolve", lambda *args, **kw: ["example"])
    calls = []
    def run(args, **kw):
        calls.append(args)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr("subprocess.run", run)
    adapter = SimpleNamespace(gateway=lambda: "192.168.1.1")
    result = ConnectivityTest(adapter).run()
    assert result["dns_working"] and result["internet_available"] and result["gateway_reachable"]
    assert result["packet_loss_percent"] is None
    assert len(calls) == 1 and calls[0][-1] == "192.168.1.1"


def test_dns_failure_and_no_gateway(monkeypatch):
    def fail(*args, **kw): raise OSError()
    monkeypatch.setattr("socket.create_connection", fail)
    monkeypatch.setattr("dns.resolver.resolve", fail)
    result = ConnectivityTest(SimpleNamespace(gateway=lambda: None)).run()
    assert result["internet_available"] is False and result["dns_working"] is False
    assert result["gateway_reachable"] is None
