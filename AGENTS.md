# AGENTS.md

> Instructions for AI coding agents working on this repository.

## Project Overview

Desktop QA utility for testing HTTP API endpoints on embedded network devices.
Built with **Python 3.13**, **PySide6** (Qt 6), managed by **uv**.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.13 |
| UI | PySide6 / Qt 6 |
| Package manager | uv |
| Linter / formatter | ruff |
| Type checker | ty |
| Tests | pytest + pytest-qt + pytest-cov |
| Build backend | hatchling |

## Architecture

- **Mixin composition** — `ApiTestApp` in `src/app/__init__.py` combines UI mixins
- **Lightweight DI container** — `src/config/di_container.py` with Protocol interfaces
- **Separation of concerns:**
  - `src/app/` — UI layer (PySide6 widgets, mixins)
  - `src/managers/` — Business logic (no Qt widget dependencies)
  - `src/config/` — Infrastructure (constants, DI, logging, JSON generation)
- **Concurrency** — `QThread` workers for non-blocking HTTP I/O
- **Enums** — `TestMode(StrEnum)` in `config/constants.py` for type-safe mode filtering

## Common Commands

```bash
# Install all dependencies (creates .venv automatically)
uv sync --group dev

# Run the app
uv run python src/main.py

# Lint
uv run ruff check src tests

# Format check
uv run ruff format --check src tests

# Type check
uv run ty check src

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src --cov-report=term-missing
```

## Code Style

- Configured in `pyproject.toml` under `[tool.ruff]`
- Line length: 100
- Quote style: double quotes
- Import sorting: isort via ruff with `known-first-party = ["app", "managers", "config"]`
- Target: Python 3.13 (use modern syntax — `X | Y` unions, etc.)
- Qt overrides keep camelCase (e.g., `closeEvent`) — add `# noqa: N802` comment

## Testing Guidelines

- Tests live in `tests/` with `test_` prefix
- `conftest.py` has shared fixtures
- Use `pytest-qt` for widget tests (`qtbot` fixture)
- `QT_QPA_PLATFORM=offscreen` for headless CI
- Test paths configured: `pythonpath = ["src"]`, `testpaths = ["tests"]`
- Widget-level tests need a real `QApplication` (via `qapp` fixture)
- Unit tests for mixins use `__new__` stubs with `MagicMock` attributes

## Project Layout

```
src/
├── main.py                  # Entry point
├── app/                     # UI layer (mixin composition)
│   ├── __init__.py          # ApiTestApp (combines mixins + graceful shutdown)
│   ├── ui_builder.py        # Layout, theme, widget wiring
│   ├── request_handling.py  # HTTP send/cancel/display
│   ├── preset_handling.py   # Preset load/save/batch queue (cached filtering)
│   ├── settings_handling.py # Persist/restore UI state (debounced auto-save)
│   └── dialogs.py           # Multi-select dialog
├── managers/                # Business logic (Qt-free)
│   ├── requests_manager.py  # QThread worker + manager (path traversal protection)
│   ├── presets.py           # Preset CRUD + JSON persistence
│   └── settings.py          # Settings JSON persistence
└── config/                  # Infrastructure
    ├── constants.py         # Paths, endpoints, theme tokens, TestMode enum
    ├── di_container.py      # DI container + Protocol interfaces
    ├── logging_system.py    # Structured logging (JSONL + text)
    └── json_generator.py    # Generate test payloads
```

## CI

GitHub Actions workflow at `.github/workflows/ci.yml` runs three parallel jobs:
1. **lint** — ruff format + lint checks
2. **type-check** — ty static analysis
3. **test** — pytest with coverage (headless Qt)

## Key Conventions

- Use Protocol-based interfaces (structural typing) for dependency injection
- Keep `managers/` free of Qt widget imports (only `QThread`/`QObject` allowed)
- All file paths go through `src/config/constants.py`
- Passwords handled as `bytearray` and zeroed after use
- JSON payloads stored in `src/config/json_configs/`
- Use `TestMode` enum (not raw strings) for happy/unhappy mode filtering
- Use `html.escape()` for any user-facing HTML rendering
- Auto-save uses debounced `QTimer` (500ms) — never save on every keystroke
- Preset list filtering is cached — call `_invalidate_preset_cache()` when presets change
- File path inputs are validated with `.resolve()` + `.relative_to()` to prevent traversal

## Security Notes

- JSON file loading validates paths stay within `JSON_FOLDER` (no directory traversal)
- HTML escaping uses `html.escape()` from stdlib (not manual replace)
- SSL verification intentionally disabled (`verify=False`) for self-signed device certs
- Username persisted in plaintext; password is **never** persisted

