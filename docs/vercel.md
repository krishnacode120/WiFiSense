# Vercel deployment

The public Vercel build is a browser-only demonstration with synthetic networks.
No Wi-Fi passwords are collected, stored, or transmitted. Authorize a demo network
to try the connection controls. State is temporary and resets on page reload.
The browser demo does not reproduce real OS roaming or continuous background service behavior.

The full Python manager remains local: serverless hosting cannot access a visitor's
Wi-Fi adapter, OS credential store, or persistent monitoring process.

Import krishnacode120/WiFiSense into Vercel with the repository root as Root Directory.
The root vercel.json installs/builds frontend and publishes frontend/dist.
It enables VITE_WIFISENSE_DEMO only for this hosted build.
Normal local development still uses FastAPI through /api.

Deployment commands:
    vercel --prod

The September 22 hosting change was uploaded without running application tests or
local verification, as requested. Vercel runs the required production build.
