import type { Snapshot } from "../types";
import { Bars, Timeline } from "../components/Charts";
export function Analytics({ data }: { data: Snapshot }) {
  const group = (event: string) =>
    Object.entries(
      data.events
        .filter((e) => e.event === event && e.ssid)
        .reduce<Record<string, number>>(
          (a, e) => ({ ...a, [e.ssid!]: (a[e.ssid!] || 0) + 1 }),
          {},
        ),
    ).map(([name, value]) => ({ name, value }));
  const averages = Object.entries(
    data.metrics.connections.reduce<Record<string, number[]>>((a, m) => {
      if (m.score !== null) (a[m.ssid] ??= []).push(m.score);
      return a;
    }, {}),
  ).map(([name, v]) => ({
    name,
    value: Math.round(v.reduce((a, b) => a + b, 0) / v.length),
  }));
  return (
    <>
      <p className="muted">
        Charts use the most recent 500 samples and 500 events. Measurements
        reflect the connected network at each point.
      </p>
      <div className="analytics-grid">
        <section className="panel">
          <h2>Signal strength over time</h2>
          <Timeline data={data.metrics.connections} />
        </section>
        <section className="panel">
          <h2>Latency over time</h2>
          <Timeline
            data={data.metrics.connections}
            field="latency_ms"
            color="#8295aa"
          />
        </section>
        <section className="panel">
          <h2>Connections per network</h2>
          <Bars data={group("connected")} label="Connections" />
        </section>
        <section className="panel">
          <h2>Average network quality</h2>
          <Bars data={averages} label="Average score" />
        </section>
        <section className="panel">
          <h2>Disconnect events</h2>
          <Bars data={group("disconnected")} label="Disconnects" />
        </section>
        <section className="panel">
          <h2>Network switches</h2>
          <Bars data={group("switched")} label="Switches" />
        </section>
      </div>
    </>
  );
}
