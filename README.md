# API Test Tool

<div align="center">

![Python](https://img.shields.io/badge/Python_3.13-3776AB?style=flat-square&logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/UI-PySide6_/_Qt6-41CD52?style=flat-square&logo=qt&logoColor=white)
![Tests](https://img.shields.io/badge/pytest-passing-0A9EDC?style=flat-square&logo=pytest&logoColor=white)
![Mypy](https://img.shields.io/badge/mypy-0_errors-2A6DB5?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square&logo=opensourceinitiative&logoColor=white)
![Platform](https://img.shields.io/badge/Windows-0078D4?style=flat-square&logo=windows&logoColor=white)

</div>

---

> **Desktop QA utility for testing HTTP API endpoints on embedded network devices.**  
> Sends authenticated HTTP requests, runs batch preset sequences, and logs every response — all from a clean two-panel UI.  
> **PySide6 · QThread · HTTP Digest auth · 0 mypy errors**

---

## Screenshot

![API Test Tool UI](docs/screenshot.png)

> Two-panel layout — request configuration sidebar (left) + response viewer (right)

---

## At a Glance

| | |
|:---|:---|
| **Language** | Python 3.13 |
| **UI Framework** | PySide6 (Qt 6) |
| **Architecture** | Mixin composition + lightweight DI container |
| **Authentication** | HTTP Digest (targets self-signed certificate devices) |
| **Concurrency** | Non-blocking `QThread` workers, cancellable mid-run |
| **Type checking** | mypy — 0 errors across 16 source files |
| **Test suite** | pytest — 4-layer coverage strategy |
| **Logging** | Plain text + structured JSONL + rotating error file |
| **Platforms** | Windows (primary), Linux, macOS |

---

## Overview

API Test Tool lets QA engineers send authenticated HTTP requests to embedded VoIP/intercom devices, run batches of pre-configured test cases, and automatically log every response — all from a clean two-panel desktop UI.

Built specifically for devices that use **self-signed certificates** and **HTTP Digest authentication**, where standard tools like Postman add too much friction to high-volume, repetitive test workflows.

---

## Features

| | |
|:---|:---|
| 🔁 **Single & batch requests** | Send one request or queue an entire preset sequence automatically |
| 🔐 **HTTP Digest auth** | Secure per-request authentication; password zeroed from memory after use |
| ✅ **Happy / unhappy modes** | Filter presets by test scenario type with one click |
| 🔍 **Live preset search** | Instant substring filter across all preset names |
| 📦 **5 payload formats** | Normal Path · Normal Action · Normal Body · Google JSON · JSON-RPC |
| ⚡ **Non-blocking UI** | All HTTP I/O on `QThread` workers — cancel mid-batch at any time |
| 💾 **Auto-save settings** | IP, credentials, window geometry, last-used preset persist between sessions |
| 📝 **Automatic logging** | Every response timestamped and written to `src/logs/` |
| 🔎 **Pretty-print JSON** | Responses are auto-formatted for readability in the viewer |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Astralborn/API-tester.git
cd API-tester

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate JSON payloads and presets (first run only)
python src/config/json_generator.py

# 4. Launch
python src/main.py
```

---

## Project Structure

```
API-tester/
├── pytest.ini
├── mypy.ini
├── requirements.txt
│
├── src/
│   ├── main.py                        # Entry point — QApplication bootstrap
│   │
│   ├── app/                           # UI layer — assembled via mixin composition
│   │   ├── __init__.py                # ApiTestApp — combines all four mixins
│   │   ├── ui_builder.py              # Two-panel layout, theme, widget wiring
│   │   ├── request_handling.py        # Send / cancel / display HTTP responses
│   │   ├── preset_handling.py         # Load / save / run presets; batch queue
│   │   ├── settings_handling.py       # Persist and restore all UI state
│   │   └── dialogs.py                 # MultiSelectDialog (batch preset picker)
│   │
│   ├── managers/                      # Business logic — no Qt dependencies
│   │   ├── requests_manager.py        # RequestWorker (QThread) + RequestManager
│   │   ├── presets.py                 # PresetManager — CRUD + JSON persistence
│   │   └── settings.py                # SettingsManager — JSON persistence
│   │
│   └── config/                        # Infrastructure
│       ├── constants.py               # Paths, API endpoints, UI theme tokens
│       ├── di_container.py            # DIContainer + Protocol interfaces
│       ├── logging_system.py          # StructuredLogger, JsonFormatter, LoggingManager
│       ├── json_generator.py          # Generates all happy + unhappy test payloads
│       └── json_configs/              # Generated payload files (git-ignored)
│
└── tests/
    ├── conftest.py                    # Shared fixtures (QApplication, mock managers)
    ├── helpers.py                     # Test utilities
    ├── test_app_widget.py             # Full ApiTestApp widget integration tests
    ├── test_di_container.py           # DIContainer + Protocol structural tests
    ├── test_dialogs.py                # MultiSelectDialog unit tests
    ├── test_logging_system.py         # StructuredLogger / formatters / manager tests
    ├── test_preset_handling.py        # PresetHandlingMixin pure-logic tests
    ├── test_preset_handling_widget.py # PresetHandlingMixin widget tests
    ├── test_preset_manager.py         # PresetManager persistence tests
    ├── test_request_handling.py       # RequestHandlingMixin unit tests
    ├── test_requests_manager.py       # RequestWorker + RequestManager tests
    ├── test_settings_handling.py      # SettingsHandlingMixin tests
    └── test_settings_manager.py       # SettingsManager persistence tests
```

---

## Generating Test Payloads

Run once before first use, or whenever endpoints change:

```bash
python src/config/json_generator.py
```

Generates `src/config/json_configs/` and `src/config/presets.json` — every combination of endpoint × format × test type:

| Type | Description |
|:---|:---|
| **Normal Path** | Method name embedded in the URL path |
| **Normal Action** | Method passed as `?action=` query parameter |
| **Normal Body** | Method name wrapped inside the JSON body |
| **Google JSON** | `apiVersion` + `method` + `params` + `context` envelope |
| **JSON-RPC** | `jsonrpc` + `method` + `params` + `id` envelope |
| **Unhappy — missing** | Empty or null required fields |
| **Unhappy — invalid** | Out-of-range or nonsensical values |
| **Unhappy — wrong types** | Strings where integers are expected, etc. |
| **Unhappy — fuzz** | XSS, SQL injection, overflow values, unicode edge cases |

---

## Supported Endpoints

| Group | Endpoints |
|:---|:---|
| **Contacts** | `GetContacts`, `SetContacts`, `RemoveContacts` |
| **SIP Accounts** | `GetSIPAccount`, `GetSIPAccounts`, `SetSIPAccount`, `SetSIPAccounts`, `RemoveSIPAccount`, `RemoveSIPAccounts`, `GetSIPAccountStatus` |
| **SIP Configuration** | `GetSIPConfiguration`, `SetSIPConfiguration` |
| **Audio Codecs** | `GetDefaultAudioCodecs`, `GetSupportedAudioCodecs`, `GetAudioCodecs`, `SetAudioCodecs` |
| **Call Control** | `Call`, `GetCallStatus`, `TerminateCall` |
| **Capabilities** | `GetServiceCapabilities`, `GetSupportedSIPAccountAttributes`, `GetSupportedMediaEncryptionModes` |

---

## Usage

1. Enter the **Device IP**
2. Enter **Username** and **Password**
3. Choose **Test mode** (`happy` / `unhappy`) — optionally search to filter presets
4. Select a **Preset** → click **Load**, or pick an **Endpoint** + **JSON file** manually
5. Click **Send Request** for a single call, or **Run Multiple** to queue a batch
6. Responses are pretty-printed and appended in the right panel
7. Logs are written automatically to `src/logs/`

---

## Logging

Each run creates a timestamped log file:

```
src/logs/log_<preset_name>_<YYYYMMDD_HHMMSS>.log
```

Multi-preset batch runs produce a single combined file with per-preset headers:

```
--- Preset: GetContacts_Normal_Path ---
--- 2025-01-15 14:32:01 ---
Tag: ok
URL: http://192.168.1.100/api/intercom/GetContacts
Payload: {}
Status Code: 200
{"contacts": [...]}
```

Three simultaneous output streams per `StructuredLogger` instance:

| Stream | File | Minimum level |
|:---|:---|:---|
| Plain text, rotating | `src/logs/<name>.log` | DEBUG |
| Structured JSONL, rotating | `src/logs/<name>_structured.jsonl` | DEBUG |
| Errors only, rotating | `src/logs/<name>_errors.log` | ERROR |

---

## Testing

```bash
python -m pytest tests               # full test suite
python -m pytest tests --cov=src     # with coverage report
python -m mypy src                   # type check (0 errors)
```

**pytest · 0 mypy errors**

| Layer | What is tested |
|:---|:---|
| **Unit — pure logic** | `_preset_matches`, `_validate_ip`, `_format_json_response`, `_escape_html`, filename sanitisation — no Qt, no I/O |
| **Unit — managers** | `PresetManager` and `SettingsManager` file I/O via `tmp_path`; `RequestManager` URL building and log creation |
| **Widget** | Full `ApiTestApp` with real `QApplication` (headless via `pytest-qt`): startup state, send/cancel flows, load/save preset, settings round-trips |
| **HTTP worker** | `RequestWorker.run()` with `requests.post` patched — success (200), non-200, network error, log output |
| **Infrastructure** | `DIContainer` register/get/singleton; all three Protocols satisfy `isinstance`; `StructuredLogger` all levels; `JsonFormatter` and `ColoredFormatter` output |

---

## Architecture

**Mixin composition** — `ApiTestApp` inherits from four focused mixins (`UIBuilderMixin`, `RequestHandlingMixin`, `PresetHandlingMixin`, `SettingsHandlingMixin`) rather than one monolithic class. Each mixin declares its required attributes via a `_*Protocol` stub class that only exists at type-check time (`TYPE_CHECKING` guard), giving full mypy coverage with zero runtime overhead.

**Dependency injection** — a lightweight `DIContainer` wires the three managers (`PresetManager`, `RequestManager`, `SettingsManager`) via structural `Protocol` interfaces, so every component is testable in isolation without touching the UI.

**Structured logging** — `StructuredLogger` wraps Python's `logging` module and writes three simultaneous streams per instance (plain text, JSONL, errors-only) with rotating file handlers. One method call — `logger.info(...)` — produces output in all three.

**Memory safety** — passwords are stored as `bytearray` and zeroed immediately after the HTTP request is made, minimising the window the plaintext exists in memory.

---

## Configuration Files

| File | Purpose |
|:---|:---|
| `pytest.ini` | Test discovery, asyncio mode, timeout settings |
| `mypy.ini` | mypy source root, PySide6/requests/urllib3 ignore rules |
| `requirements.txt` | Runtime + dev dependencies |
| `src/config/presets.json` | Saved presets (git-ignored, generated by `json_generator.py`) |
| `src/settings.json` | Persisted UI state (git-ignored, created on first run) |

---

## .gitignore Additions

```gitignore
# Generated at runtime — do not commit
src/config/json_configs/
src/config/presets.json
src/settings.json
src/logs/

# Standard Python
__pycache__/
*.pyc
.venv/
.mypy_cache/
```

---

## License

MIT — free to use in internal QA and automation workflows.

---

## Author

**Stanislav Nikolaievskyi** · [github.com/Astralborn](https://github.com/Astralborn)

*Portfolio project — desktop application architecture with Python and PySide6.*
