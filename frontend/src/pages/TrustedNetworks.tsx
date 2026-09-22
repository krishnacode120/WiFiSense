import { Plus, ShieldCheck } from "lucide-react";
import type { Trusted } from "../types";
import { displayDate } from "../services/api";
export function TrustedNetworks({
  networks,
  busy,
  run,
  add,
}: {
  networks: Trusted[];
  busy: boolean;
  run: (p: string, m?: string, b?: unknown, s?: string) => void;
  add: () => void;
}) {
  return (
    <>
      <div className="section-toolbar">
        <p className="muted">
          Only these networks can be managed automatically.
        </p>
        <button className="button primary" onClick={add}>
          <Plus size={15} />
          Add trusted network
        </button>
      </div>
      <div className="trusted-grid">
        {networks.length ? (
          networks.map((t) => (
            <section className="panel trusted-card" key={t.id}>
              <div className="panel-heading">
                <h2>{t.ssid}</h2>
                <ShieldCheck size={18} />
              </div>
              <p className="muted">
                {t.security} · {t.bssid || "Any matching access point"}
              </p>
              <label className="setting-toggle">
                <span>Allow auto-connect</span>
                <input
                  type="checkbox"
                  checked={t.auto_connect_enabled}
                  disabled={busy}
                  onChange={(e) =>
                    run("/wifi/trusted/" + t.id, "PATCH", {
                      auto_connect_enabled: e.target.checked,
                    })
                  }
                />
              </label>
              <label>
                Priority (-10 to 10)
                <input
                  aria-label={"Priority for " + t.ssid}
                  type="number"
                  min="-10"
                  max="10"
                  defaultValue={t.priority}
                  onBlur={(e) => {
                    const value = Number(e.target.value);
                    if (
                      Number.isInteger(value) &&
                      value >= -10 &&
                      value <= 10 &&
                      value !== t.priority
                    )
                      run("/wifi/trusted/" + t.id, "PATCH", {
                        priority: value,
                      });
                  }}
                />
              </label>
              <small>
                Last connected:{" "}
                {t.last_connected_at
                  ? displayDate(t.last_connected_at)
                  : "Never"}
              </small>
              <div className="card-actions">
                <button
                  className="button"
                  disabled={busy}
                  onClick={() =>
                    run(
                      "/wifi/connect/" + t.id,
                      "POST",
                      undefined,
                      "Network connected",
                    )
                  }
                >
                  Connect
                </button>
                <button
                  className="text-button danger"
                  disabled={busy}
                  onClick={() => {
                    if (
                      window.confirm(
                        "Remove " +
                          t.ssid +
                          " from trusted networks and delete its WiFiSense credential?",
                      )
                    )
                      run(
                        "/wifi/trusted/" + t.id,
                        "DELETE",
                        undefined,
                        "Network removed",
                      );
                  }}
                >
                  Forget network
                </button>
              </div>
            </section>
          ))
        ) : (
          <section className="panel empty">
            <ShieldCheck size={24} />
            <h2>No trusted networks</h2>
            <p>Add a network you own or are authorized to use.</p>
            <button className="button primary" onClick={add}>
              Add trusted network
            </button>
          </section>
        )}
      </div>
    </>
  );
}
