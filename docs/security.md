# Security model

Only explicitly authorized entries with user-provided credentials may be connected
by WiFiSense. No profile import, password recovery, cracking, sniffing, injection,
WPS attacks, bypass or deauthentication exists in this project.

## Credentials

System mode explicitly selects Windows Credential Manager or Linux Secret Service.
No generic keyring backend chain is trusted: insecure fallback stores are rejected.
Credential-store failures are user-safe errors. Passwords are never stored in SQLite,
returned by endpoints, printed, interpolated into shell commands or included in logs.
Pydantic SecretStr protects repr; validation error handlers also discard rejected
input and exception contexts. Python cannot guarantee zeroization of immutable
strings in process memory, so local process compromise remains outside this boundary.

## Local API

Bind to 127.0.0.1. Host validation prevents DNS rebinding to arbitrary hostnames.
Origin checks restrict browser access to the documented localhost dashboard origins.
State changes require the X-WiFiSense header, preventing ordinary cross-site forms;
CORS does not permit hostile-origin preflight requests. Non-loopback clients are
rejected. The header is a CSRF control, not an authentication secret.

Other programs running as the same local user can call the API. This is a personal
single-user service, not a privilege boundary against malicious local applications.
Do not expose it through a reverse proxy, public tunnel or LAN binding. Multi-user
access needs authentication, TLS, user isolation and a separate threat review.

## Network identity and operations

SSID, security and optional BSSID must match both before and after connection.
BSSID locking narrows selection but does not prevent a sophisticated impersonating
access point. WPA2/WPA3 authentication is provided by the OS. Open networks require
explicit authorization and provide no link encryption.

Adapters use fixed command names, subprocess argument arrays, bounded timeouts and
redacted errors. All native connection profiles created by WiFiSense disable OS
autoconnect. Existing unrelated OS profiles are neither imported nor modified;
the OS can still independently connect to them outside WiFiSense.

Only the gateway, one fixed external TCP endpoint (1.1.1.1:443), and one DNS query
(example.com) are checked after a trusted connection. These checks reveal ordinary
connection metadata to those services and may follow a VPN or Ethernet default route.
There is no port-range, subnet, packet capture or traffic interception code.

## Repository hygiene

.env, SQLite files, virtual environments, logs, dependency folders, and browser
test artifacts are ignored. Commit only synthetic fixtures and screenshots.
Use scripts/check_repository.py against staged files before publishing.
If a real secret is ever committed, rotate it and clean Git history before publishing.
