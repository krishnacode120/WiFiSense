# Setup reference

See the root README for startup commands. Copy backend/.env.example to backend/.env
only if needed. Run Uvicorn from backend so .env is resolved predictably.

| Environment variable | Default | Purpose |
| --- | --- | --- |
| WIFISENSE_MODE | simulation | simulation or system |
| WIFISENSE_DATABASE_URL | mode-specific SQLite file | optional DB override |
| WIFISENSE_INTERFACE | empty | exact adapter name; required if multiple adapters |

The default binds only to loopback. Vite proxies /api to port 8000. After npm run build,
restart the backend to mount static assets. Client pages use in-app navigation so
there are no server-side deep-link rewrites.

## Windows system integration milestone

The adapter will encapsulate netsh discovery and native WLAN connection calls.
Run as the logged-in desktop user so Credential Manager is available. Enable Wi-Fi,
WLAN AutoConfig and location permission if Windows requires it for BSSID discovery.
Never grant administrator privileges merely to bypass an unexplained adapter error.

## Linux system integration milestone

Use a distribution with NetworkManager/nmcli, an unlocked Secret Service keyring
and its session D-Bus. Headless installations without secure Secret Service must
use simulation until a secure credential backend is provisioned.
Do not run the application as root as a substitute for proper policy permissions.

## Checks

Backend: pytest from backend. Frontend: npm run build from frontend.
Browser test: npm test; ports 8000 and 5173 must be free. Windows uses Edge;
Linux needs Playwright Chromium. Browser tests use a temporary database and
simulation-only credentials. No real Wi-Fi changes occur during automated checks.
