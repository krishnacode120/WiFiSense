# Setup reference

See the root README for startup commands. Copy backend/.env.example to backend/.env
only if needed. Run Uvicorn from backend so .env is resolved predictably.

| Environment variable | Default | Purpose |
| --- | --- | --- |
| WIFISENSE_MODE | system | system mode |
| WIFISENSE_DATABASE_URL | mode-specific SQLite file | optional DB override |
| WIFISENSE_INTERFACE | empty | exact adapter name; required with multiple adapters |

Use one Uvicorn worker. The service accepts loopback clients only. Vite proxies /api
to port 8000. After npm run build, restart the backend to mount compiled assets.
The UI uses in-app navigation; no server-side deep-link rewrites are needed.

## Windows

Python 3.11+, Node.js 22+, an English-language Windows installation, netsh, WLAN
AutoConfig, and a working Wi-Fi adapter are required. Windows Credential Manager
is accessed as the logged-in user; no separate secret service is needed.
Recent Windows versions may require location permission to show SSIDs/BSSIDs.

The adapter uses netsh only to discover interfaces/networks and query state/gateway.
Native WlanConnect receives a temporary XML profile in memory. The temporary
profile disables automatic OS connection and includes the selected access point.
No password-bearing file is created or imported, and no password enters process
arguments. The native buffer is cleared after the call; Python strings may remain
in process memory until released. Connection success is verified by querying the OS.

Supported: Open, WPA2-Personal (AES), WPA3-Personal where the OS/driver supports it.
WEP and enterprise/EAP connections are rejected. Leading/trailing-space SSIDs,
localized netsh output and unusual driver formats may fail closed. RSSI is null
because netsh reports percentage; missing band labels may be inferred from channel
and cannot reliably distinguish 6 GHz on older output formats.

Set WIFISENSE_INTERFACE to the exact name (for example Wi-Fi) if more than one adapter
is present. The adapter will not arbitrarily choose one. Wi-Fi must be enabled.
Do not grant administrator access merely to bypass an unexplained error.

Implementation references:
[WlanConnect](https://learn.microsoft.com/en-us/windows/win32/api/wlanapi/nf-wlanapi-wlanconnect),
[connection parameters](https://learn.microsoft.com/en-us/windows/win32/api/wlanapi/ns-wlanapi-wlan_connection_parameters),
[BSSID list](https://learn.microsoft.com/en-us/windows/win32/nativewifi/dot11-bssid-list).

## Linux

Use a distribution with NetworkManager/nmcli, a Wi-Fi adapter, an unlocked Secret
Service keyring and its session D-Bus. Keyring installs SecretStorage on Linux.
A GNOME Keyring or compatible Secret Service implementation must already be installed
and running. Headless sessions without a secure backend fail closed in system mode.

The adapter creates an in-memory NetworkManager connection with save=no and
autoconnect=no. PSK flags are set to not-saved. Activation receives the credential
through a pipe consumed by nmcli's passwd-file /dev/stdin support.
No plaintext secret file, shell interpolation or password argument is used.
Only this process's own temporary profiles are cleaned up; unrelated profiles are
not touched. If the process crashes, a non-autoconnecting in-memory profile may
remain until NetworkManager restarts.

Open, WPA2-Personal and WPA3-Personal are supported. EAP, WEP and hidden networks
are outside scope. Choose the exact interface, such as wlan0, when there is more
than one. Appropriate NetworkManager policy permissions are required; do not run
the application as root instead of configuring your desktop session.

References: [nmcli commands and password-file format](https://networkmanager.pages.freedesktop.org/NetworkManager/NetworkManager/nmcli.html),
[secret flags and key management](https://networkmanager.pages.freedesktop.org/NetworkManager/NetworkManager/nm-settings-nmcli.html).

## Tests and limitations

Backend: pytest from backend. Frontend: npm run build from frontend.
Browser test: npm test; ports 8000 and 5173 must be free. Windows uses installed Edge;
Linux needs npx playwright install --with-deps chromium.
Tests start a temporary test database and never change real Wi-Fi.

Native adapters have parser and mocked command/API tests. No live hardware connection
has been verified in this project workspace. Validate both platforms on authorized
test hardware before relying on automatic roaming. OS-managed auto-connect settings
for existing profiles remain independent of WiFiSense.
