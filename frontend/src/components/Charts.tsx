import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  BarChart,
  Bar,
} from "recharts";
import type { Metric } from "../types";
const tooltip = {
  background: "#ffffff",
  border: "1px solid #dfe3e8",
  borderRadius: 10,
  color: "#354253",
};
export function Timeline({
  data,
  field = "signal_strength",
  color = "#648cb9",
}: {
  data: Metric[];
  field?: "signal_strength" | "latency_ms" | "score";
  color?: string;
}) {
  if (!data.length)
    return (
      <div className="chart-empty">
        Connect a trusted network to start collecting measurements.
        <span>
          History is sampled periodically, so the first points may take a
          moment.
        </span>
      </div>
    );
  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data.map((m) => ({
            ...m,
            time: new Date(
              m.timestamp + (!/[Z+]/.test(m.timestamp) ? "Z" : ""),
            ).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          }))}
        >
          <defs>
            <linearGradient id={"fill-" + field} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.25} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid
            vertical={false}
            stroke="#e8ecf1"
            strokeDasharray="3 5"
          />
          <XAxis
            dataKey="time"
            stroke="#83919f"
            tickLine={false}
            axisLine={false}
            minTickGap={50}
            fontSize={11}
          />
          <YAxis
            domain={field === "latency_ms" ? ["auto", "auto"] : [0, 100]}
            stroke="#83919f"
            tickLine={false}
            axisLine={false}
            width={32}
            fontSize={11}
          />
          <Tooltip contentStyle={tooltip} />
          <Area
            type="monotone"
            dataKey={field}
            name={
              field === "latency_ms"
                ? "Latency (ms)"
                : field === "score"
                  ? "Quality score"
                  : "Signal (%)"
            }
            stroke={color}
            strokeWidth={1.5}
            fill="transparent"
            connectNulls={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
export function Bars({
  data,
  label,
}: {
  data: { name: string; value: number }[];
  label: string;
}) {
  return data.length ? (
    <div className="chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <XAxis dataKey="name" stroke="#83919f" fontSize={11} />
          <YAxis stroke="#83919f" fontSize={11} />
          <Tooltip contentStyle={tooltip} />
          <Bar
            dataKey="value"
            name={label}
            fill="#819ab8"
            radius={[5, 5, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  ) : (
    <div className="chart-empty">No measurements yet.</div>
  );
}
