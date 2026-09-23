import { useState } from "react";
import {
  Activity,
  BarChart3,
  Check,
  History,
  LayoutDashboard,
  Menu,
  Radio,
  RefreshCw,
  Settings2,
  ShieldCheck,
  Wifi,
  X,
} from "lucide-react";
import { useNetwork } from "./hooks/useNetwork";
import { api } from "./services/api";
import type { Network, Settings } from "./types";
import { NetworkList } from "./components/NetworkList";
import { TrustDialog } from "./components/TrustDialog";
import { SettingsPage } from "./pages/SettingsPage";
import { Dashboard } from "./pages/Dashboard";
import { Analytics } from "./pages/Analytics";
import { TrustedNetworks } from "./pages/TrustedNetworks";
import { HistoryPage } from "./pages/HistoryPage";
const nav = [
  { name: "Dashboard", icon: LayoutDashboard },
  { name: "Nearby Networks", icon: Radio },
  { name: "Trusted Networks", icon: ShieldCheck },
  { name: "Connection History", icon: History },
  { name: "Analytics", icon: BarChart3 },
  { name: "Settings", icon: Settings2 },
];
const subtitles: Record<string, string> = {
  Dashboard: "Connection status and trusted networks.",
  "Nearby Networks": "Wireless networks detected by your adapter.",
  "Trusted Networks": "Manage authorized networks and connection preferences.",
  "Connection History": "Connection changes and management actions.",
  Analytics: "Recent signal and connection measurements.",
  Settings: "Automatic selection, ranking, and monitoring.",
};
export default function App() {
  const { data, error, loading, refresh } = useNetwork();
  const [page, setPage] = useState("Dashboard"),
    [trust, setTrust] = useState<Network | null | undefined>(undefined),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [actionError, setActionError] = useState(""),
    [filter, setFilter] = useState(""),
    [menu, setMenu] = useState(false);
  async function action(
    path: string,
    method = "POST",
    body?: unknown,
    success = "Changes saved",
  ) {
    setBusy(true);
    setActionError("");
    setMessage("");
    try {
      await api(path, method, body);
      await refresh();
      setMessage(success);
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Operation failed");
      throw e;
    } finally {
      setBusy(false);
    }
  }
  const run = (
    path: string,
    method = "POST",
    body?: unknown,
    success?: string,
  ) => {
    void action(path, method, body, success).catch(() => {});
  };
  const navigate = (name: string) => {
    setPage(name);
    setMenu(false);
    setFilter("");
  };
  const networkList = (networks: Network[]) => (
    <NetworkList
      networks={networks}
      onTrust={setTrust}
      onConnect={(id) =>
        run("/wifi/connect/" + id, "POST", undefined, "Network connected")
      }
      busy={busy}
    />
  );
  return (
    <div className="app-shell">
      <aside className={"sidebar " + (menu ? "open" : "")}>
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            navigate("Dashboard");
          }}
        >
          <Wifi size={24} />
          <span>
            WiFiSense<small>Connection manager</small>
          </span>
        </a>
        <nav aria-label="Main navigation">
          {nav.map((item) => (
            <button
              aria-label={item.name}
              key={item.name}
              className={"nav-item " + (page === item.name ? "selected" : "")}
              onClick={() => navigate(item.name)}
            >
              <item.icon size={17} />
              {item.name}
              {item.name === "Nearby Networks" && (
                <span className="nav-count">{data?.networks.length || 0}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="local-status">
            <span className={data && !error ? "status-dot" : "offline-dot"} />
            <span>
              {data && !error ? "Local service running" : "Service unavailable"}
              <small>WiFiSense 1.0.0</small>
            </span>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <button
            className="icon-button mobile-menu"
            aria-label="Toggle navigation"
            onClick={() => setMenu(!menu)}
          >
            {menu ? <X size={19} /> : <Menu size={19} />}
          </button>
          <span>Wi-Fi connection manager</span>
          <span className="mode-label">
            {"System mode"}
          </span>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <h1>{page}</h1>
              <p>{subtitles[page]}</p>
            </div>
            <button
              className="button"
              disabled={busy}
              onClick={() => void refresh()}
            >
              <RefreshCw size={14} />
              Refresh
            </button>
          </div>
          {(error || actionError || data?.system.error) && (
            <div className="error" role="alert">
              {error || actionError || data?.system.error}
            </div>
          )}
          {message && (
            <div className="notice" role="status">
              <Check size={16} />
              {message}
              <button
                className="icon-button"
                aria-label="Dismiss notification"
                onClick={() => setMessage("")}
              >
                <X size={15} />
              </button>
            </div>
          )}
          {loading && !data ? (
            <div className="panel empty">
              <Activity size={22} />
              <h2>Loading connections…</h2>
            </div>
          ) : !data ? (
            <div className="panel empty">
              <Wifi size={24} />
              <h2>Local Wi-Fi service required</h2>
              <p>
                Start the local backend and frontend to manage your computer’s Wi-Fi. Cloud hosting cannot access your adapter.
              </p>
              <a className="button primary" href="http://127.0.0.1:8000">Open local dashboard</a>
              <a href="https://github.com/krishnacode120/WiFiSense#quick-start--windows-powershell">Setup instructions</a>
            </div>
          ) : (
            <>
              {page === "Dashboard" && (
                <Dashboard
                  data={data}
                  busy={busy}
                  run={run}
                  navigate={navigate}
                  networkList={networkList}
                />
              )}
              {page === "Nearby Networks" && (
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>
                        Available networks{" "}
                        <span className="count">{data.networks.length}</span>
                      </h2>
                      <p className="muted">
                        Untrusted networks cannot connect automatically.
                      </p>
                    </div>
                    <input
                      className="search"
                      aria-label="Search networks"
                      placeholder="Search networks…"
                      value={filter}
                      onChange={(e) => setFilter(e.target.value)}
                    />
                  </div>
                  {networkList(
                    data.networks.filter((x) =>
                      x.ssid.toLowerCase().includes(filter.toLowerCase()),
                    ),
                  )}
                </section>
              )}
              {page === "Trusted Networks" && (
                <TrustedNetworks
                  networks={data.trusted}
                  busy={busy}
                  run={run}
                  add={() => setTrust(null)}
                />
              )}
              {page === "Connection History" && (
                <HistoryPage
                  events={data.events}
                  filter={filter}
                  setFilter={setFilter}
                />
              )}
              {page === "Analytics" && <Analytics data={data} />}
              {page === "Settings" && (
                <SettingsPage
                  key={JSON.stringify(data.settings)}
                  initial={data.settings}
                  trusted={data.trusted}
                  busy={busy}
                  onSave={async (s: Settings) => {
                    await action("/settings", "PUT", s, "Settings saved");
                  }}
                />
              )}
            </>
          )}
        </main>
      </div>
      {trust !== undefined && (
        <TrustDialog
          network={trust}
          onClose={() => setTrust(undefined)}
          onSave={async (body) => {
            await action(
              "/wifi/trusted",
              "POST",
              body,
              "Network added to your trusted list",
            );
          }}
        />
      )}
    </div>
  );
}
