"""Isolated browser-test server. Never accesses real Wi-Fi or the OS keyring."""
from pathlib import Path
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
sys.path.insert(0, str(root / "backend" / "tests"))
import uvicorn
from app.config import Config
from app.main import create_app
from fakes import FakeWifiAdapter, FakeCredentialStore, FakeConnectivity

with tempfile.TemporaryDirectory(prefix="wifisense-e2e-") as directory:
    adapter = FakeWifiAdapter()
    app = create_app(
        Config(database_url=f"sqlite:///{Path(directory) / 'test.db'}"),
        adapter=adapter, credential_store=FakeCredentialStore(),
        connectivity=FakeConnectivity(adapter),
    )
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning", access_log=False)
