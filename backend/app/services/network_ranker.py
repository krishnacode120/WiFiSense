from app.schemas import Settings


def score_network(signal, measurements, stability, priority, preferred, settings: Settings):
    measurements = measurements or {}
    internet = measurements.get("internet_available")
    latency = measurements.get("latency_ms")
    components = {
        "signal": signal,
        "connectivity": 50 if internet is None else (100 if internet else 0),
        "latency": 50 if latency is None else max(0, 100 - latency / 2),
        "stability": stability,
    }
    base = sum(components[k] * settings.weights[k] for k in components)
    return round(max(0, min(100, base + priority + (5 if preferred else 0))), 1)


def trusted_match(network, trusted):
    return network.ssid == trusted.ssid and network.security == trusted.security and (not trusted.bssid or (network.bssid or "").lower() == trusted.bssid)
