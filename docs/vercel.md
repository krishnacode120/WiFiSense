# Vercel and local Wi-Fi

WiFiSense uses real Windows WLAN or Linux NetworkManager APIs. There is no
runtime simulation or browser demo. A remotely hosted browser page cannot
control the visitor's Wi-Fi adapter or access their OS credential manager.

The Vercel build displays local-service setup instructions and a link to
http://127.0.0.1:8000. It does not proxy Wi-Fi commands or collect credentials.
Build the frontend locally and start the Python backend to use that address,
or use the local Vite development server on port 5173.

Import krishnacode120/WiFiSense with the repository root as Root Directory.
The root vercel.json installs and builds frontend and publishes frontend/dist.
No demo environment variable is used. A configured Vercel project can deploy
GitHub pushes automatically; uploading code alone does not create a deployment.

The native-only update was made without running tests or a local build at the
user's request. Real hardware behavior has not been verified.
