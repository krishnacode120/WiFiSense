import threading
import time
import uuid
from datetime import timedelta
from sqlalchemy import select, delete
from app.adapters.base_wifi_adapter import WifiError
from app.models import TrustedNetwork, Setting, ConnectionEvent, NetworkHistory, SignalHistory, utcnow
from app.schemas import Settings
from app.services.wifi_scanner import WifiScanner
from app.services.network_ranker import score_network, trusted_match
from app.services.roaming_manager import RoamingManager
from app.services.signal_analyzer import get_signal_quality, percentage_rating
from app.utils.logging import logger


def public_trust(n):
    return {k: getattr(n, k) for k in ("id", "ssid", "bssid", "security", "auto_connect_enabled", "priority", "created_at", "updated_at", "last_connected_at")}


class NetworkManager:
    def __init__(self, adapter, credentials, sessions, mode, connectivity):
        self.adapter, self.credentials, self.sessions = adapter, credentials, sessions
        self.mode, self.connectivity = mode, connectivity
        self.scanner, self.roaming = WifiScanner(adapter), RoamingManager()
        self.lock = threading.RLock()
        self.settings = Settings()
        with sessions() as db:
            saved = db.get(Setting, mode)
            if saved:
                self.settings = Settings.model_validate(saved.value)
        self.measurements = {}
        self.samples = {}
        self.failures = {}
        self.last_metrics = float("-inf")
        self.current = None
        self.connected_since = None
        self.observed_identity = None
        self.internet_before = None
        self.last_error = None

    def audit(self, event, ssid=None, detail=""):
        with self.sessions() as db:
            db.add(ConnectionEvent(event=event, ssid=ssid, detail=detail, mode=self.mode))
            db.commit()
        # Log only the event enum. User-supplied strings and errors never reach logs.
        logger.info(event)

    def trusted(self):
        with self.sessions() as db:
            return list(db.scalars(select(TrustedNetwork).where(TrustedNetwork.mode == self.mode)))

    def trust(self, payload):
        with self.lock:
            if any(n.ssid == payload.ssid and n.bssid == payload.bssid for n in self.trusted()):
                raise WifiError("This network is already trusted")
            identity = str(uuid.uuid4())
            if payload.password:
                self.credentials.save_credential(identity, payload.password.get_secret_value())
            try:
                with self.sessions() as db:
                    n = TrustedNetwork(id=identity, mode=self.mode, **payload.model_dump(exclude={"password", "authorized"}))
                    db.add(n)
                    db.commit()
                    result = public_trust(n)
            except Exception:
                self.credentials.delete_credential(identity)
                raise WifiError("Could not save the trusted network") from None
            self.audit("trusted_added", payload.ssid)
            return result

    def update_trust(self, identity, payload):
        with self.lock, self.sessions() as db:
            n = db.get(TrustedNetwork, identity)
            if not n or n.mode != self.mode:
                raise WifiError("Trusted network was not found")
            for key, value in payload.model_dump(exclude_none=True).items():
                setattr(n, key, value)
            n.updated_at = utcnow()
            db.commit()
            self.audit("trusted_updated", n.ssid)
            return public_trust(n)

    def forget(self, identity):
        with self.lock, self.sessions() as db:
            n = db.get(TrustedNetwork, identity)
            if not n or n.mode != self.mode:
                raise WifiError("Trusted network was not found")
            self.credentials.delete_credential(identity)
            db.delete(n)
            db.commit()
            self.roaming.reset()
            if self.settings.preferred_network == identity:
                self.save_settings(self.settings.model_copy(update={"preferred_network": None}))
            self.audit("trusted_removed", n.ssid)

    def save_settings(self, value):
        with self.lock:
            if value.preferred_network and value.preferred_network not in {n.id for n in self.trusted()}:
                raise WifiError("Preferred network must be trusted")
            with self.sessions() as db:
                db.merge(Setting(key=self.mode, value=value.model_dump()))
                db.commit()
            self.settings = value
            self.roaming.reset()
            self.audit("settings_updated")
            return value

    @staticmethod
    def identity(n):
        return (n.ssid, n.bssid) if n else None

    def scan(self, force=False):
        with self.lock:
            networks = self.scanner.scan(self.settings.scan_interval, force)
            trusted = self.trusted()
            for n in networks:
                matches = sorted((t for t in trusted if trusted_match(n, t)), key=lambda t: (bool(t.bssid), t.priority), reverse=True)
                t = matches[0] if matches else None
                n.trusted, n.trusted_id = bool(t), t.id if t else None
                n.connected = self.identity(n) == self.identity(self.current)
                if t:
                    cached = self.measurements.get(self.identity(n))
                    data = cached[1] if cached and time.monotonic() - cached[0] <= 300 else None
                    sample = self.samples.get(self.identity(n), [])
                    stability = 100 * sum(sample) / len(sample) if sample and data is not None else 50
                    quality = get_signal_quality(n.rssi)["quality"] if n.rssi is not None else n.signal_strength
                    n.score = score_network(quality, data, stability, t.priority, t.id == self.settings.preferred_network, self.settings)
            return sorted(networks, key=lambda n: (n.score if n.score is not None else -1, n.signal_strength), reverse=True)

    def observe(self):
        current = self.adapter.get_current_network()
        identity = self.identity(current)
        if identity != self.observed_identity:
            if self.observed_identity:
                self.audit("disconnected", self.observed_identity[0])
            if current:
                self.audit("connected", current.ssid)
            self.connected_since = time.monotonic() if current else None
            self.internet_before = None
            self.observed_identity = identity
        self.current = current
        return current

    def check_connectivity(self):
        if not self.current:
            return
        # Only probe explicitly trusted current networks.
        if not any(trusted_match(self.current, n) for n in self.trusted()):
            return
        data = self.connectivity.run()
        identity = self.identity(self.current)
        self.measurements[identity] = (time.monotonic(), data)
        self.samples.setdefault(identity, []).append(bool(data["internet_available"]))
        self.samples[identity] = self.samples[identity][-20:]
        online = data["internet_available"]
        if self.internet_before is not None and self.internet_before != online:
            self.audit("internet_restored" if online else "internet_lost", self.current.ssid)
        self.internet_before = online

    def connect(self, identity, automatic=False):
        with self.lock:
            trusted = next((n for n in self.trusted() if n.id == identity), None)
            if not trusted or (automatic and not trusted.auto_connect_enabled):
                raise WifiError("Connection requires an explicitly authorized trusted network")
            networks = self.scan(force=True)
            available = [n for n in networks if trusted_match(n, trusted)]
            if not available:
                raise WifiError("Trusted network is unavailable or its security has changed")
            target = max(available, key=lambda n: n.signal_strength)
            current = self.observe()
            if current and trusted_match(current, trusted):
                return self.status()
            previous = current
            password = self.credentials.get_credential(identity) if trusted.security != "Open" else None
            if trusted.security != "Open" and not password:
                self.failures[identity] = time.monotonic() + max(30, self.settings.roaming_cooldown)
                self.audit("connection_failed", trusted.ssid, "credential unavailable")
                raise WifiError("Credential is unavailable; remove and re-add this trusted network")
            self.audit("connection_requested", trusted.ssid, "automatic" if automatic else "manual")
            try:
                self.adapter.connect(target, password)
                del password
                current = self.adapter.get_current_network()
                if not current or not trusted_match(current, trusted):
                    self.adapter.disconnect()
                    raise WifiError("The operating system did not confirm the authorized network")
            except Exception:
                self.failures[identity] = time.monotonic() + max(30, self.settings.roaming_cooldown)
                self.audit("connection_failed", trusted.ssid)
                raise WifiError("Connection failed; check the passphrase, adapter permissions, and network availability") from None
            self.observe()
            self.roaming.switched(time.monotonic())
            if previous and self.identity(previous) != self.identity(current):
                self.audit("switched", current.ssid)
            with self.sessions() as db:
                n = db.get(TrustedNetwork, identity)
                n.last_connected_at = utcnow()
                db.commit()
            self.check_connectivity()
            self.persist_metrics(force=True)
            return self.status()

    def disconnect(self):
        with self.lock:
            # Explicit disconnect must not be immediately undone by automation.
            self.save_settings(self.settings.model_copy(update={"auto_connect": False}))
            self.adapter.disconnect()
            self.observe()
            self.audit("disconnect_requested")
            return self.status()

    def status(self):
        with self.lock:
            self.observe()
            current = self.current
            if current:
                current = current.model_copy()
                current.quality = get_signal_quality(current.rssi)["rating"] if current.rssi is not None else percentage_rating(current.signal_strength) + " (estimated)"
                decorated = next((n for n in self.scan() if self.identity(n) == self.identity(current)), None)
                if decorated:
                    current = current.model_copy(update={"trusted": decorated.trusted, "trusted_id": decorated.trusted_id, "score": decorated.score})
            measured = self.measurements.get(self.identity(current))
            if measured and (time.monotonic() - measured[0] > 300 or not current or not current.trusted):
                measured = None
            return {"network": current, "connectivity": measured[1] if measured else None,
                    "measurement_age_seconds": round(time.monotonic() - measured[0]) if measured else None,
                    "connection_duration_seconds": round(time.monotonic() - self.connected_since) if self.connected_since else 0,
                    "auto_connect": self.settings.auto_connect, "mode": self.mode}

    def persist_metrics(self, force=False):
        now = time.monotonic()
        if not force and now - self.last_metrics < self.settings.history_interval:
            return
        networks = self.scan()
        measured = self.measurements.get(self.identity(self.current))
        data = measured[1] if measured else {}
        with self.sessions() as db:
            for n in networks:
                db.add(SignalHistory(ssid=n.ssid, mode=self.mode, signal_strength=n.signal_strength, rssi=n.rssi))
                if n.connected:
                    db.add(NetworkHistory(ssid=n.ssid, bssid=n.bssid, mode=self.mode, signal_strength=n.signal_strength,
                                          score=n.score, latency_ms=data.get("latency_ms"), internet_available=data.get("internet_available"), dns_working=data.get("dns_working")))
            cutoff = utcnow() - timedelta(days=30)
            for model in (SignalHistory, NetworkHistory, ConnectionEvent):
                db.execute(delete(model).where(model.timestamp < cutoff, model.mode == self.mode))
            db.commit()
        self.last_metrics = now

    def tick(self):
        with self.lock:
            self.observe()
            self.check_connectivity()
            networks = self.scan()
            enabled = {n.id for n in self.trusted() if n.auto_connect_enabled}
            now = time.monotonic()
            candidates = [n for n in networks if n.trusted_id in enabled and n.signal_strength >= self.settings.minimum_signal and self.failures.get(n.trusted_id, 0) <= now]
            if self.settings.auto_connect and candidates:
                best = candidates[0]
                current = next((n for n in networks if n.connected), None)
                if not self.current:
                    self.connect(best.trusted_id, automatic=True)
                elif current and current.trusted and self.settings.smart_roaming and not best.connected:
                    if self.roaming.should_switch((best.trusted_id, best.bssid), best.score, current.score or 0, now, self.settings):
                        self.connect(best.trusted_id, automatic=True)
                else:
                    self.roaming.reset()
            else:
                self.roaming.reset()
            self.persist_metrics()
            self.last_error = None
