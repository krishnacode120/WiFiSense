import { Wifi } from "lucide-react";
import type { Network } from "../types";
export function NetworkList({
  networks,
  onTrust,
  onConnect,
  busy,
}: {
  networks: Network[];
  onTrust: (n: Network) => void;
  onConnect: (id: string) => void;
  busy: boolean;
}) {
  if (!networks.length)
    return (
      <div className="empty">
        <Wifi size={25} />
        <h3>No matching networks</h3>
        <p>Use Nearby Networks to find and authorize a connection.</p>
      </div>
    );
  return (
    <div className="table-wrap">
      <table className="network-table">
        <thead>
          <tr>
            <th>Network</th>
            <th>Signal</th>
            <th>Security</th>
            <th>Channel / Band</th>
            <th>Trust</th>
            <th>
              <span className="sr-only">Action</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {networks.map((n) => (
            <tr className="network-row" key={n.ssid + n.bssid}>
              <td>
                <strong>{n.ssid || "Hidden network"}</strong>
                <small className="network-id">
                  {n.bssid || "BSSID unavailable"}
                </small>
              </td>
              <td>
                <div className="signal-cell">
                  <div className="signal-track">
                    <i style={{ width: n.signal_strength + "%" }} />
                  </div>
                  <span>{n.signal_strength}%</span>
                </div>
                <small>
                  {n.rssi !== null ? n.rssi + " dBm" : "OS estimate"}
                  {n.score !== null ? " · Score " + n.score : ""}
                </small>
              </td>
              <td>{n.security}</td>
              <td>
                {n.channel ?? "—"}
                <small className="network-id">{n.band || "Unknown band"}</small>
              </td>
              <td>
                <span className={n.trusted ? "trusted-text" : "muted"}>
                  {n.trusted ? "Trusted" : "Untrusted"}
                </span>
              </td>
              <td className="row-action">
                {n.connected ? (
                  <span className="connection-state online">Connected</span>
                ) : n.trusted ? (
                  <button
                    className="button small"
                    disabled={busy}
                    onClick={() => onConnect(n.trusted_id!)}
                  >
                    Connect
                  </button>
                ) : (
                  <button
                    className="button small"
                    disabled={
                      busy ||
                      !n.ssid ||
                      !["Open", "WPA2-Personal", "WPA3-Personal"].includes(
                        n.security,
                      )
                    }
                    onClick={() => onTrust(n)}
                  >
                    Trust network
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
