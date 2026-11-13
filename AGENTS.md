Project title: SmartDrive IVI Bluetooth Simulator (QA workshop)
Project description: Software-only simulator of IVI Bluetooth pairing, connection, reconnection, and call interruption. Not for production or vehicle use.
Folder structure (create as needed):
- docs/ - SRS and test docs
- src/bluetooth/ - simulator
- tests/unit, tests/api, tests/ui, tests/capl - tests
- test-data/bluetooth-devices.json - fixtures
- defects/ - defect reports
Tech stack or framework: Python, Pytest; Playwright only if a web UI exists. CAPL (Vector CANoe) scripts are a supplement only, under tests/capl/; follow SRS 6.1 (DOC-CAPL-001..003).
Naming conventions and formatting: snake_case files/functions, PascalCase classes. Requirement ID in test names (e.g. test_fr_bt_003_...) and docstrings (FR-BT-003). Keep code and docs concise; use tables/bullets, no filler.
Sensitive data handling: Synthetic data only. No real device IDs, passkeys, or personal data. Do not read .env files except .env.example.
Custom documentation & source: docs/SmartDrive_IVI_Specification_1_Bluetooth_Connectivity.md is the source of truth (FR-BT-001..008, NFR-BT-001..005, OQ-01..08). Defaults: pairing timeout 30 s, max 5 paired devices, one active smartphone connection. Read only the sections needed.
Rules:
- SRS is treated as the dev/product-owner requirement; edit it only when the user explicitly asks (v1.1: CAPL supplement added).
- OQ-01..08 are unresolved: never assume answers; flag them as clarification questions and mark dependent tests blocked.
- Every test, scenario, and defect traces to a requirement ID.
- Workflow order: requirement review -> owner feedback -> test design -> automation -> execution/defects.