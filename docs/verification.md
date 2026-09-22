# Verification record

Verified locally on Windows with Python 3.13 and Node.js 22.
The project targets Python 3.11+; CI also exercises Python 3.11 on Windows and Linux.

## Automated checks

- Backend pytest: 59 tests passed.
- Python modules compiled and API OpenAPI routes inspected.
- TypeScript strict checking and Vite production build passed.
- Browser tests exercise desktop and mobile: explicit trust authorization, secure-input
  submission, connection, status, all six pages, settings persistence, disconnection,
  no page errors, and responsive viewport behavior.
- Backend integration tests cover sustained roaming, failure backoff, missing-credential
  fallback, trusted-only selection, mode separation, history throttling and internet events.
- Credential redaction tested across validation errors, API responses, database schema/data
  and connection failures.
- Windows tests cover parsing, ambiguous/missing interfaces, native temporary profile
  parameters, BSSID selection and XML escaping.
- Linux tests cover escaped nmcli fields, stdin-only secrets, nonpersistent/nonautomatic
  profile options, disabled radio and failed activation cleanup.
- npm dependency audit reported no known vulnerabilities at installation time.

Browser fixtures are synthetic. Screenshots in docs/screenshots contain no real
network identity or credentials. They represent the redesigned light desktop UI.

## Not verified

- Real Windows or Linux adapter connection, roaming, driver behavior or WPA3 compatibility.
- Live OS keyring roundtrip on this host (automated tests use memory/mocked backends).
- Interface-isolated gateway/DNS/internet routing in the presence of VPNs or Ethernet.
- Captive portals, enterprise authentication, hidden SSIDs, or multiple simultaneous adapters.
- Long-duration operation and retention behavior over 30 actual days.

These are limitations, not claims of completed hardware validation.
