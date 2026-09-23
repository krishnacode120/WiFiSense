from contextlib import asynccontextmanager
from pathlib import Path
import sys
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import Config
from app.database import make_database
from app.adapters.base_wifi_adapter import WifiError
from app.services.credential_store import CredentialStore
from app.services.connectivity_test import ConnectivityTest
from app.services.network_manager import NetworkManager
from app.services.monitoring_service import MonitoringService
from app.api.routes import router


def create_app(config=None, adapter=None, credential_store=None, monitor=True, connectivity=None):
    config = config or Config()

    @asynccontextmanager
    async def lifespan(app):
        selected = adapter
        if selected is None:
            if sys.platform == "win32":
                from app.adapters.windows_wifi_adapter import WindowsWifiAdapter
                selected = WindowsWifiAdapter(config.interface)
            elif sys.platform.startswith("linux"):
                from app.adapters.linux_wifi_adapter import LinuxWifiAdapter
                selected = LinuxWifiAdapter(config.interface)
            else:
                raise WifiError("This operating system is unsupported")
        engine, sessions = make_database(config.database)
        app.state.manager = NetworkManager(selected, credential_store or CredentialStore(config.mode), sessions, config.mode, connectivity if connectivity is not None else ConnectivityTest(selected))
        app.state.monitor = MonitoringService(app.state.manager) if monitor else None
        if app.state.monitor:
            app.state.monitor.start()
        try:
            yield
        finally:
            if app.state.monitor:
                app.state.monitor.stop()
            engine.dispose()

    app = FastAPI(title="WiFiSense", version="1.0.0", lifespan=lifespan)
    origins = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000", "http://127.0.0.1:8000"]
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Content-Type", "X-WiFiSense"])
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "[::1]", "testserver"])

    @app.middleware("http")
    async def local_only(request: Request, call_next):
        if request.client and request.client.host not in {"127.0.0.1", "::1", "testclient"}:
            return JSONResponse({"detail": "WiFiSense accepts local requests only"}, status_code=403)
        origin = request.headers.get("origin")
        if origin and origin not in origins:
            return JSONResponse({"detail": "Origin is not allowed"}, status_code=403)
        if request.method not in {"GET", "HEAD", "OPTIONS"} and request.headers.get("X-WiFiSense") != "local-dashboard":
            return JSONResponse({"detail": "Local dashboard header is required"}, status_code=403)
        try:
            return await call_next(request)
        except Exception:
            # Never let a low-level exception dump request input or credentials to a server log.
            from app.utils.logging import logger
            logger.error("request_internal_error")
            return JSONResponse({"detail": "Operation failed; check service and adapter availability"}, status_code=500)

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        # Pydantic's default errors include rejected input (potentially the password).
        return JSONResponse({"detail": "Invalid request; check fields and passphrase requirements",
                             "fields": [".".join(str(p) for p in e["loc"]) for e in exc.errors()]}, status_code=422)

    @app.exception_handler(WifiError)
    async def wifi_error(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=409)

    @app.exception_handler(Exception)
    async def unexpected(request, exc):
        return JSONResponse({"detail": "Operation failed; check service and adapter availability"}, status_code=500)

    app.include_router(router)
    dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if dist.exists():
        app.mount("/", StaticFiles(directory=dist, html=True), name="dashboard")
    return app


app = create_app()
