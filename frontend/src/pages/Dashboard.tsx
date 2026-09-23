import { Activity, ArrowUpRight, Clock3, Power, Wifi } from "lucide-react";
import type { Snapshot, Network } from "../types";
import { Timeline } from "../components/Charts";
import { displayDate } from "../services/api";
function duration(s: number) {
  return s >= 3600
    ? Math.floor(s / 3600) + "h " + Math.floor((s % 3600) / 60) + "m"
    : Math.floor(s / 60) + "m " + (s % 60) + "s";
}
export function Dashboard({
  data,
  busy,
  run,
  navigate,
  networkList,
}: {
  data: Snapshot;
  busy: boolean;
  run: (path: string) => void;
  navigate: (page: string) => void;
  networkList: (n: Network[]) => React.ReactNode;
}) {
  const c = data.current,
    n = c.network;
  return (
    <>
      <section className="panel current-panel">
        <div className="connection-heading">
          <div className="connection-title">
            <Wifi size={24} />
            <div>
              <div className="overline">CURRENT CONNECTION</div>
              <h2>{n?.ssid || "Not connected"}</h2>
              <p>
                {n
                  ? n.security + " · " + (n.band || "Band unavailable")
                  : "Choose an authorized network to connect."}
              </p>
            </div>
          </div>
          <div className="connection-actions">
            <span className={"connection-state " + (n ? "online" : "")}>
              {n ? "Connected" : "Disconnected"}
            </span>
            {n ? (
              <button
                className="button"
                disabled={busy}
                onClick={() => run("/wifi/disconnect")}
              >
                <Power size={14} />
                Disconnect
              </button>
            ) : (
              <button
                className="button primary"
                onClick={() => navigate("Nearby Networks")}
              >
                Choose network
              </button>
            )}
          </div>
        </div>
        <dl className="connection-readings">
          <div>
            <dt>Signal</dt>
            <dd>{n ? n.signal_strength + "%" : "—"}</dd>
            <small>{n?.quality || "No measurement"}</small>
          </div>
          <div>
            <dt>Internet</dt>
            <dd>
              {c.connectivity
                ? c.connectivity.internet_available
                  ? "Online"
                  : "Unavailable"
                : "Not checked"}
            </dd>
            <small>
              {c.connectivity
                ? "DNS " +
                  (c.connectivity.dns_working ? "working" : "unavailable")
                : "Checked on trusted networks"}
            </small>
          </div>
          <div>
            <dt>Latency</dt>
            <dd>
              {c.connectivity?.latency_ms != null
                ? c.connectivity.latency_ms + " ms"
                : "—"}
            </dd>
            <small>TCP connection time</small>
          </div>
          <div>
            <dt>Quality score</dt>
            <dd>{n?.score != null ? n.score.toFixed(1) + " / 100" : "—"}</dd>
            <small>Weighted connection quality</small>
          </div>
          <div>
            <dt>Connected for</dt>
            <dd>{duration(c.connection_duration_seconds)}</dd>
            <small>
              {n?.trusted
                ? "Authorized network"
                : n
                  ? "Not in trusted list"
                  : "No active connection"}
            </small>
          </div>
        </dl>
        <div className="connection-options">
          <label className="inline-check">
            <input
              type="checkbox"
              aria-label="Enable auto connect"
              checked={c.auto_connect}
              disabled={busy}
              onChange={(e) =>
                run(
                  "/wifi/auto-connect/" +
                    (e.target.checked ? "enable" : "disable"),
                )
              }
            />
            Auto-connect to trusted networks
          </label>
          <button className="text-button" onClick={() => navigate("Settings")}>
            Connection settings <ArrowUpRight size={14} />
          </button>
        </div>
      </section>
      <section className="panel networks-panel">
        <div className="panel-heading">
          <div>
            <h2>
              Trusted networks in range{" "}
              <span className="count">
                {data.networks.filter((x) => x.trusted).length}
              </span>
            </h2>
            <p className="muted">Sorted by connection quality.</p>
          </div>
          <button
            className="button"
            onClick={() => navigate("Nearby Networks")}
          >
            All nearby networks <ArrowUpRight size={14} />
          </button>
        </div>
        {networkList(data.networks.filter((x) => x.trusted))}
      </section>
      <div className="lower-grid">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Signal history</h2>
              <p className="muted">
                Sampled every {data.settings.history_interval} seconds
              </p>
            </div>
            <span className="chart-key">Signal (%)</span>
          </div>
          <Timeline data={data.metrics.connections} />
        </section>
        <section className="panel">
          <div className="panel-heading">
            <h2>Recent events</h2>
            <button
              className="text-button"
              onClick={() => navigate("Connection History")}
            >
              View history <ArrowUpRight size={14} />
            </button>
          </div>
          <div className="activity-list">
            {data.events.length ? (
              data.events.slice(0, 5).map((e) => (
                <div className="activity-item" key={e.id}>
                  <Activity size={14} />
                  <div>
                    <strong>{e.event.replaceAll("_", " ")}</strong>
                    <p>{e.ssid || "Application settings"}</p>
                  </div>
                  <time>{displayDate(e.timestamp)}</time>
                </div>
              ))
            ) : (
              <div className="empty compact">
                <Clock3 size={22} />
                <p>No events recorded yet.</p>
              </div>
            )}
          </div>
        </section>
      </div>
      <div className="monitor-note">
        <span
          className={data.system.monitoring ? "status-dot" : "offline-dot"}
        />
        {data.system.monitoring
          ? "Monitoring every " + data.settings.monitoring_interval + " seconds"
          : "Monitoring stopped"}
        {c.measurement_age_seconds !== null
          ? " · Last check " + c.measurement_age_seconds + "s ago"
          : ""}
      </div>
    </>
  );
}
