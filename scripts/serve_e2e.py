"""Isolated simulation server for browser tests; never touches a user's DB or keyring."""
import os
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import uvicorn
from app.config import Config
from app.main import create_app

with tempfile.TemporaryDirectory(prefix="wifisense-e2e-") as directory:
    app = create_app(Config(mode="simulation", database_url=f"sqlite:///{Path(directory) / 'test.db'}"))
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning", access_log=False)
