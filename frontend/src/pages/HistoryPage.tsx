import { History } from "lucide-react";
import type { Event } from "../types";
import { displayDate } from "../services/api";
export function HistoryPage({
  events,
  filter,
  setFilter,
}: {
  events: Event[];
  filter: string;
  setFilter: (s: string) => void;
}) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Connection & audit log</h2>
        <input
          className="search"
          aria-label="Filter history"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter events or networks…"
        />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Event</th>
              <th>Network</th>
              <th>Details</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {events
              .filter((e) =>
                (e.event + " " + e.ssid)
                  .toLowerCase()
                  .includes(filter.toLowerCase()),
              )
              .map((e) => (
                <tr key={e.id}>
                  <td>
                    <span className="event-pill">
                      {e.event.replaceAll("_", " ")}
                    </span>
                  </td>
                  <td>{e.ssid || "—"}</td>
                  <td>{e.detail || "—"}</td>
                  <td>{displayDate(e.timestamp)}</td>
                </tr>
              ))}
          </tbody>
        </table>
        {!events.length && (
          <div className="empty">
            <History size={22} />
            <p>No recorded events yet.</p>
          </div>
        )}
      </div>
      <p className="muted footnote">Latest 500 events · 30-day retention</p>
    </section>
  );
}
