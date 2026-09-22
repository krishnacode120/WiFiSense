# Architecture and scoring

WiFiSense runs one FastAPI process, a single background monitoring thread, and an
SQLAlchemy session per operation. A reentrant manager lock serializes trust changes,
connection actions and monitor decisions. Blocking adapter calls run in FastAPI's
worker threads, not its event loop. Launch with one Uvicorn worker.

## Trust boundary

The adapter does not decide authorization. NetworkManager resolves a persisted
trusted ID, checks the current mode, SSID, security and optional BSSID, re-scans
before activation, retrieves only that ID's credential, then confirms the actual
connection. OS-saved profiles never imply trust. Deleted entries cannot participate
in later selections. Manual connections can use entries with automatic selection off.

Credentials are keyed by random trusted-entry IDs to distinguish access points and
security profiles. SQLite has no credential columns. Simulation credentials exist
only in memory. The default DB name and all queries are scoped by mode.

## Ranking

Default score:

```
0.55 × signal + 0.20 × connectivity + 0.15 × latency + 0.10 × stability
```

Signal is an approximate piecewise RSSI quality (anchors -100:0, -75:40, -67:60,
-60:80, -50:90, -30:100), or the OS percentage when RSSI is unavailable.
Do not interpret an OS percentage as measured dBm.

Connectivity is 100 for a successful TCP reachability probe and 0 for failure.
Latency score is max(0, 100 - TCP handshake milliseconds / 2).
Stability is the success percentage of the last 20 probe samples in this process.
Unmeasured components use 50; historical measurements expire after five minutes.
The dashboard labels unmeasured connectivity as not checked. Network quality history
is persisted for analytics; ranking's recent sample cache resets on restart.

Weights are finite non-negative numbers normalized to sum 1.
User priority (-10 to +10) is added, and a preferred-network ID adds 5 points.
Clamp the final score to 0–100. This makes priority a bounded preference rather than
a way to bypass trust, minimum signal, or failed-connection backoff.

Example: signal 80, connectivity 100, latency score 80, stability 90 gives 85.
This calculation deliberately uses the documented formula rather than copying
numerically inconsistent example totals.

## Roaming

Automatic selection is off initially. When disconnected it chooses the top eligible
trusted network. A connection to an untrusted network established outside WiFiSense
is displayed but is not probed or automatically replaced.

On a trusted connection, a different candidate must exceed the current score by
15 points continuously for 15 seconds. Defaults include a 60-second cooldown;
loss of advantage resets the candidate timer. Timing uses monotonic clocks.
Scan caching respects scan interval; monitoring checks every five seconds by default.
The OS may perform access-point roaming within an unpinned SSID; WiFiSense manages
network-level changes, not forced reconnection to a different BSSID of the same entry.

## Storage and monitoring

Tables: trusted_networks, settings, network_history, signal_history, connection_events.
create_all establishes the initial schema; future schema changes require migrations.
SQLite uses WAL and a five-second busy timeout. Default history sampling is 30 seconds,
with one immediate sample on connection. Queries are bounded and history uses offsets.
Thirty-day retention is pruned during sampling.

Audit events include connected, disconnected, switched, connection_failed,
internet_lost/restored, connection_requested, disconnect_requested, trusted_added/
updated/removed and settings_updated. Runtime logs contain only fixed event names.

## Extension points

Adapters isolate OS commands. ConnectivityTest can gain interface-bound probes.
NetworkRanker can gain new normalized components without changing authorization.
RoamingManager is a deterministic state machine. A future remote/desktop layer
must preserve server-side trust and introduce real authentication before LAN access.
