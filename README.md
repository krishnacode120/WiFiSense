# WiFiSense
### Intelligent Wi-Fi Auto-Selection and Secure Connection Manager

A local-first Wi-Fi manager with a responsive React dashboard, FastAPI service,
quality-based ranking, trusted-network authorization, and sustained-improvement roaming.
Designed for education and management of your own networks.

**No cracking, password discovery, interception, authentication bypass, deauthentication,
packet injection, or unauthorized connections.** Every managed connection must match
an explicitly authorized database entry. Credentials must be supplied by the user.

## Features

- Nearby SSID/BSSID, signal, security, band/channel, connected and trusted status.
- OS keyring credential storage in system mode; ephemeral memory in simulation.
- Weighted signal, internet availability, latency and stability ranking.
- User priorities, preferred network, per-network automation controls.
- Hysteresis, cooldown and failure backoff; manual disconnect pauses automation.
- Lightweight connectivity checks for the connected, trusted network.
- SQLite history, audit events, periodic metrics, and 30-day retention.
- Six dashboard pages with Recharts analytics, responsive layout, readable errors.
- Default simulation mode, initially empty trusted list, auto-connect initially disabled.
- Local-only API with Host, Origin and mutation-header checks.

## Architecture

```mermaid
graph TD
    A[React Dashboard] --> B[FastAPI Backend]
    B --> C[Wi-Fi Manager]
    B --> D[SQLite: metadata and metrics only]
    C --> K[OS credential keyring]
    C --> E[Adapter Layer]
    E --> F[Windows Adapter]
    E --> G[Linux Adapter]
    E --> H[Simulation Adapter]
    F --> I[Operating System Wi-Fi Subsystem]
    G --> I
```

See [architecture](docs/architecture.md), [security](docs/security.md), and [setup](docs/setup.md).

## Requirements

Python 3.11+, Node.js 22+, npm, Git. Real mode additionally needs a supported wireless
adapter, user-session access to an unlocked secure keyring, and WLAN/NetworkManager permissions.
Use one backend process (one worker) so only one manager controls the adapter.

## Quick start — Windows PowerShell

From the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
cd backend
$env:WIFISENSE_MODE="simulation"
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5173. Use **Nearby Networks → Trust network**, enter a
made-up simulation passphrase (8–63 characters), explicitly authorize the network,
then connect. Add Home_5G and Home_2G to try ranking. Enable auto-connect in Settings.

The simulated environment cannot touch your real Wi-Fi adapter. Networks are
**not automatically trusted**, even if their example names resemble your own network.
Simulation credentials vanish on restart; remove and re-add secured simulation entries
after restarting. Open-network simulation entries do not need a passphrase.

## Linux setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
cd backend
WIFISENSE_MODE=simulation ../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# separate terminal, repository root:
cd frontend
npm ci
npm run dev
```

## Real system mode

Stop the simulation backend, set `WIFISENSE_MODE=system`, and restart it.
System and simulation use separate databases by default and mode-scoped records even
when a custom database URL is shared. Never reuse simulation credentials for real networks.

```powershell
$env:WIFISENSE_MODE="system"
# Optional exact adapter name:
$env:WIFISENSE_INTERFACE="Wi-Fi"
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Linux: `WIFISENSE_MODE=system WIFISENSE_INTERFACE=wlan0 ../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.

Windows and Linux adapter implementations are included in separate phase commits.
See setup documentation for supported security types and platform limitations.
No saved OS profiles are implicitly imported as trusted networks.

## Production assets, local hosting

```bash
cd frontend
npm run build
```

Restart the backend after building. It serves the compiled dashboard at
http://127.0.0.1:8000. Development uses Vite's `/api` proxy.
Do not expose this personal single-user service to the LAN or internet.

## API

Interactive schema: http://127.0.0.1:8000/docs. Write requests must include
`X-WiFiSense: local-dashboard`; credentials are write-only and validation responses
omit rejected inputs. Example endpoint inventory:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | /api/wifi/current | Current network and connectivity |
| GET | /api/wifi/scan | Cached/rate-limited nearby scan |
| GET, POST | /api/wifi/trusted | List / explicitly authorize |
| PATCH, DELETE | /api/wifi/trusted/{id} | Priority, automation / forget |
| POST | /api/wifi/connect/{id} | Connect an authorized network |
| POST | /api/wifi/disconnect | Disconnect and pause automation |
| POST | /api/wifi/auto-connect/enable | Enable automatic selection |
| POST | /api/wifi/auto-connect/disable | Disable automatic selection |
| GET | /api/wifi/history | Audit events; limit and offset |
| GET | /api/wifi/metrics | Recent signal and connection samples |
| GET, PUT | /api/settings | Read / validate settings |
| GET | /api/system/status | Mode, adapter, monitor and error status |

## Testing

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -q
cd ../frontend
npm run build
npm test
```

Linux uses `../.venv/bin/python -m pytest -q`. For browser tests on Linux,
first run `npx playwright install --with-deps chromium`.
Windows browser tests use installed Microsoft Edge.
Browser tests start their own isolated simulation backend on port 8000 and Vite on
5173; stop development servers on those ports first. They exercise trust, connect,
all six pages, settings persistence, disconnect, desktop and mobile layout.
Automated tests never need a real wireless adapter.

## Screenshots

![WiFiSense light desktop dashboard](docs/screenshots/dashboard-desktop.png)

[Mobile dashboard](docs/screenshots/dashboard-mobile.png). These are synthetic simulation
fixtures from the verified browser workflow. See [verification record](docs/verification.md).

## Troubleshooting

- Backend unavailable: start port 8000 first; open the UI on exactly localhost or 127.0.0.1.
- No trusted candidates: explicitly authorize a visible network and enable its automation.
- Keyring unavailable: unlock your login keyring; never install a plaintext fallback.
- Wrong password: remove and re-add the trusted entry; failures back off before retrying.
- Simulation credential unavailable after restart: re-add that simulated network.
- No internet: TCP endpoint or DNS may be blocked; this is not captive-portal detection.
- Native adapter errors: verify radio, WLAN service / NetworkManager, location permission,
  selected interface and OS language. See [setup](docs/setup.md).
- Frontend `npm` points to a broken global shim: use the npm bundled with your Node installation.

## Security & limitations

Read [security](docs/security.md). This is a single-user local service, not an authenticated
multi-user LAN controller. Existing OS Wi-Fi auto-connect behavior remains independent;
WiFiSense never modifies unrelated OS profiles. SSID/BSSID are not cryptographic
network identities. Enterprise Wi-Fi, WEP, captive portals, hidden networks and
multi-adapter routing need additional work. Packet-loss percentage remains null
because one lightweight probe is insufficient to estimate it responsibly.
Measurements can use the OS default route (including VPN/Ethernet); they are not
guaranteed to isolate the Wi-Fi interface. Native hardware validation is separate
from simulated and mocked testing.

## GitHub & contributions

Repository: https://github.com/krishnacode120/WiFiSense

See [contribution guidelines](CONTRIBUTING.md).

```bash
git init
git branch -M main
git status
git add .
git commit -m "Initial commit: WiFiSense - simulated end-to-end build"
gh repo create WiFiSense --public --source=. --remote=origin --description "Intelligent Wi-Fi auto-selection and secure connection manager (educational/personal use)"
git push -u origin main
```

If necessary, run `gh auth login` interactively. Never paste an access token into a
source file. Before every push, inspect staged paths and run the repository hygiene
check. MIT licensed. Submit focused pull requests with tests; all future features must
preserve explicit trust authorization.

## Future improvements

First, validate the native adapters on controlled Windows and Linux test hardware.
Then consider desktop packaging, captive-portal detection, notifications, report
exports, device-bound quality probes and schema migrations. Raspberry Pi, ESP32,
multi-device monitoring, heatmaps and ML prediction are extension points, not implemented
features.
