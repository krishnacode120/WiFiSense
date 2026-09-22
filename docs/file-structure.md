# Completed project structure

```text
WiFiSense/
├── .github/workflows/ci.yml
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/__init__.py
│   │   ├── schemas/__init__.py
│   │   ├── api/routes.py
│   │   ├── adapters/
│   │   │   ├── base_wifi_adapter.py
│   │   │   ├── simulated_wifi_adapter.py
│   │   │   ├── windows_wifi_adapter.py
│   │   │   ├── windows_wlan.py
│   │   │   └── linux_wifi_adapter.py
│   │   ├── services/
│   │   │   ├── credential_store.py
│   │   │   ├── signal_analyzer.py
│   │   │   ├── connectivity_test.py
│   │   │   ├── network_ranker.py
│   │   │   ├── network_manager.py
│   │   │   ├── wifi_scanner.py
│   │   │   ├── roaming_manager.py
│   │   │   └── monitoring_service.py
│   │   └── utils/logging.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_api.py
│   │   ├── test_core.py
│   │   ├── test_connectivity.py
│   │   ├── test_windows_adapter.py
│   │   └── test_linux_adapter.py
│   ├── .env.example
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── styles.css
│   │   ├── components/{Charts,NetworkList,TrustDialog}.tsx
│   │   ├── pages/{Dashboard,Analytics,HistoryPage,TrustedNetworks,SettingsPage}.tsx
│   │   ├── hooks/useNetwork.ts
│   │   ├── services/api.ts
│   │   └── types/index.ts
│   ├── tests/workflow.spec.ts
│   ├── playwright.config.ts
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── package.json
│   └── package-lock.json
├── docs/
│   ├── architecture.md
│   ├── security.md
│   ├── setup.md
│   ├── verification.md
│   ├── file-structure.md
│   └── screenshots/{dashboard-desktop,dashboard-mobile}.png
├── scripts/
│   ├── check_repository.py
│   ├── serve_e2e.py
│   ├── run-backend.ps1
│   └── run-frontend.ps1
├── .gitignore
├── .gitattributes
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

The Nearby Networks page is composed in App.tsx from the reusable network table.
Empty Python package initializer files are omitted from this tree for readability.
Runtime databases, environments, build outputs and dependency folders are ignored.
