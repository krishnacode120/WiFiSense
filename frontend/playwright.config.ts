import { defineConfig, devices } from "@playwright/test";
const python =
  process.platform === "win32"
    ? "../.venv/Scripts/python.exe"
    : "../.venv/bin/python";
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  timeout: 60000,
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: "off",
    screenshot: "only-on-failure",
    channel: process.platform === "win32" ? "msedge" : undefined,
  },
  projects: [
    {
      name: "desktop",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 1050 },
      },
    },
    {
      name: "mobile",
      use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" },
    },
  ],
  webServer: [
    {
      command: '"' + python + '" ../scripts/serve_e2e.py',
      url: "http://127.0.0.1:8000/api/system/status",
      reuseExistingServer: false,
      timeout: 60000,
    },
    {
      command: "node node_modules/vite/bin/vite.js --host 127.0.0.1",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: false,
      timeout: 60000,
    },
  ],
});
