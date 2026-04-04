# API Test Tool

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?logo=qt&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-passing-brightgreen?logo=pytest&logoColor=white)
![Coverage](https://img.shields.io/badge/Coverage-100%25%20modules-green?logo=codecov&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?logo=opensourceinitiative&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

</div>

---

> **Desktop QA utility for testing REST API endpoints on embedded network devices.**
> Sends authenticated HTTP requests, runs batch preset sequences, and logs every response — all from a clean two-panel UI.
> Built with **PySide6** · Async via **QThread** · **HTTP Digest auth** · **100% module coverage**

---

## At a Glance

| | |
|:---|:---|
| **Language** | Python 3.10+ |
| **UI Framework** | PySide6 (Qt 6) |
| **Architecture** | Mixin composition + DI container |
| **Auth** | HTTP Digest (self-signed certificate devices) |
| **Concurrency** | Non-blocking QThread workers, cancellable mid-run |
| **Test suite** | pytest · 100% coverage per runtime module |
| **Logging** | Plain text + rotating file + structured JSONL |
| **Platforms** | Windows (primary), Linux, macOS |

---

## Overview

API Test Tool lets QA engineers send authenticated HTTP requests to embedded devices, run batches of pre-configured test cases, and automatically log every response — all from a clean two-panel desktop UI.

Built for devices that use **self-signed certificates** and **HTTP Digest authentication**, where standard tools like Postman add friction to repetitive test workflows.

---

## Features

| | |
|:---|:---|
| 🔁 **Single & batch requests** | Send one request or run a full preset sequence automatically |
| 🔐 **HTTP Digest auth** | Username + password on every request |
| ✅ **Happy / unhappy modes** | Filter presets by test scenario type |
| 🔍 **Searchable presets** | Find and load any preset instantly |
| 📦 **Multiple payload formats** | Normal Path / Action / Body, Google JSON, JSON-RPC |
| ⚡ **Non-blocking UI** | Async requests via QThread — cancel mid-run at any time |
| 💾 **Auto-save settings** | IP, username, window state persist between sessions |
| 📝 **Automatic logging** | Every response timestamped and written to `logs/` |

---

## Screenshot

![API Test Tool UI](docs/screenshot.png)

> Two-panel layout — request configuration sidebar (left) + response viewer (right)

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/Astralborn/API-tester.git
cd API-tester

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate test payloads and presets (first time only)
python src/config/json_generator.py

# 4. Run
python src/main.py
```

---

## Project Structure

```
src/
├── main.py                       # Entry point
│
├── app/                          # UI layer (mixin composition)
│   ├── __init__.py               # ApiTestApp — assembles all mixins
│   ├── ui_builder.py             # Two-panel layout & theme
│   ├── request_handling.py       # Send / cancel requests
│   ├── preset_handling.py        # Load / save / run presets
│   ├── settings_handling.py      # Persist and restore UI state
│   └── dialogs.py                # MultiSelectDialog
│
├── managers/                     # Business logic
│   ├── requests_manager.py       # HTTP worker (QThread) + RequestManager
│   ├── presets.py                # PresetManager — CRUD + persistence
│   └── settings.py               # SettingsManager — JSON persistence
│
└── config/                       # Infrastructure & test data
    ├── constants.py              # Paths, endpoints, theme tokens
    ├── di_container.py           # DI container + Protocol interfaces
    ├── logging_system.py         # Structured logger + JSON output + rotation
    ├── json_generator.py         # Generates all happy + unhappy payloads
    └── json_configs/             # Generated JSON files (git-ignored)
```

---

## Generating Test Payloads

Run once before first use, or whenever endpoints change:

```bash
python src/config/json_generator.py
```

Creates the full `json_configs/` folder and `presets.json` with every combination of endpoint × format × test type:

| Type | Description |
|:---|:---|
| **Normal Path** | Method name in URL path |
| **Normal Action** | Method as `?action=` query param |
| **Normal Body** | Method name wrapped inside JSON body |
| **Google JSON** | `apiVersion` + `method` + `params` + `context` |
| **JSON-RPC** | `jsonrpc` + `method` + `params` + `id` |
| **Unhappy — no data** | Empty / null values |
| **Unhappy — invalid** | Out-of-range or nonsensical inputs |
| **Unhappy — wrong types** | Strings where ints expected, etc. |
| **Unhappy — fuzz** | XSS, SQL injection, overflow, unicode |

---

## Supported Endpoints

| Group | Endpoints |
|:---|:---|
| **Contacts** | `GetContacts`, `SetContacts`, `RemoveContacts` |
| **SIP Accounts** | `GetSIPAccount(s)`, `SetSIPAccount(s)`, `RemoveSIPAccount(s)`, `GetSIPAccountStatus` |
| **SIP Configuration** | `GetSIPConfiguration`, `SetSIPConfiguration` |
| **Audio Codecs** | `GetDefaultAudioCodecs`, `GetSupportedAudioCodecs`, `GetAudioCodecs`, `SetAudioCodecs` |
| **Call Control** | `Call`, `GetCallStatus`, `TerminateCall` |
| **Capabilities** | `GetServiceCapabilities`, `GetSupportedSIPAccountAttributes`, `GetSupportedMediaEncryptionModes` |

---

## Usage

1. Enter the **Device IP**
2. Enter **Username** and **Password**
3. Choose **Test mode** (`happy` / `unhappy`) and optionally search presets
4. Select a **Preset** → **Load** it, or pick **Endpoint** + **JSON file** manually
5. Click **Send Request** for a single call — or **Run Multiple** for a batch
6. View formatted JSON responses in the right panel
7. Logs are saved automatically to `logs/`

---

## Logging

Each request is logged automatically:

```
logs/log_<preset_name>_<YYYYMMDD_HHMMSS>.log
```

Multi-preset runs produce a single combined file with per-preset separators:

```
--- Preset: GetContacts_Normal_Path ---
--- 2025-01-15 14:32:01 ---
Tag: ok
URL: http://192.168.1.100/api/intercom/GetContacts
Payload: {}
Status Code: 200
{"contacts": [...]}
```

---

## Testing

```bash
pip install -r requirements.txt
python -m pytest tests                        # all tests, ~5 s
python -m pytest tests --cov=src              # with coverage report
```

**All tests passing · 100% coverage per runtime module**

| Layer | What's tested |
|:---|:---|
| **Unit** | Pure-logic methods via `__new__` + `MagicMock` — no Qt needed |
| **Widget** | Full `ApiTestApp` with real `QApplication` (headless, via `pytest-qt`) |
| **Persistence** | File I/O round-trips via `pytest`'s `tmp_path` fixture |
| **HTTP worker** | `RequestWorker.run()` with `requests.post` patched — no real network |

Every runtime application module sits at **100% coverage**. The only excluded files are `main.py` (entry point `__main__` block) and `json_generator.py` (dev utility script).

---

## Architecture Notes

The app is assembled via **mixin composition** — `ApiTestApp` inherits from four focused mixins rather than one monolithic class. Dependencies are injected through a lightweight `DIContainer` using `Protocol`-based interfaces, making individual components independently testable.

Logging uses a custom `StructuredLogger` that writes plain text, rotating file, and structured JSONL output simultaneously.

---

## .gitignore Recommendations

```gitignore
# Application data (generated at runtime)
src/config/json_configs/
src/logs/
src/config/presets.json
src/settings.json

# Python
__pycache__/
*.pyc
.venv/
```

---

## License

MIT — free to use in internal QA and automation workflows.

---

## Author

**Stanislav Nikolaievskyi** · [github.com/Astralborn](https://github.com/Astralborn)

*Portfolio project demonstrating desktop application architecture with Python and PySide6.*
