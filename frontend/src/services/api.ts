import { hostedDemo } from "./environment";
import type { Snapshot } from "../types";
export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  if (hostedDemo) {
    const { demoApi } = await import("./hostedDemo");
    return demoApi<T>(path, method, body);
  }
  const response = await fetch("/api" + path, {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-WiFiSense": "local-dashboard",
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: AbortSignal.timeout(60000),
  });
  if (!response.ok) {
    const data = await response
      .json()
      .catch(() => ({ detail: "The service did not respond" }));
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Request failed. Check your inputs.",
    );
  }
  return response.json();
}
export async function snapshot(): Promise<Snapshot> {
  const [current, networks, trusted, events, metrics, system, settings] =
    await Promise.all([
      api<Snapshot["current"]>("/wifi/current"),
      api<Snapshot["networks"]>("/wifi/scan"),
      api<Snapshot["trusted"]>("/wifi/trusted"),
      api<Snapshot["events"]>("/wifi/history?limit=500"),
      api<Snapshot["metrics"]>("/wifi/metrics"),
      api<Snapshot["system"]>("/system/status"),
      api<Snapshot["settings"]>("/settings"),
    ]);
  return { current, networks, trusted, events, metrics, system, settings };
}
export function displayDate(s: string) {
  return new Date(s + (!/[Z+]/.test(s) ? "Z" : "")).toLocaleString();
}
