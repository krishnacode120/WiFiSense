import threading
from app.adapters.base_wifi_adapter import WifiError
from app.utils.logging import logger


class MonitoringService:
    def __init__(self, manager):
        self.manager = manager
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run, name="wifisense-monitor", daemon=True)

    def start(self):
        self.thread.start()

    def run(self):
        while not self.stop_event.is_set():
            try:
                self.manager.tick()
            except WifiError as exc:
                self.manager.last_error = str(exc)
                logger.warning("monitor_adapter_error")
            except Exception:
                self.manager.last_error = "Monitoring failed; inspect adapter availability and database permissions"
                logger.error("monitor_internal_error")
            self.stop_event.wait(self.manager.settings.monitoring_interval)

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=50)
