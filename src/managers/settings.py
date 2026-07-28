"""Settings manager for API Test Tool."""
from __future__ import annotations

import json
from typing import Any, Final

from config.constants import TestMode, resource_path
from config.logging_system import get_logger

_logger = get_logger("settings_manager")


class SettingsManager:
    """Manages application settings persistence via a JSON file."""

    SETTINGS_FILE: Final[str] = "settings.json"

    def __init__(self) -> None:
        """Initialise the manager and load settings from disk."""
        self.settings_file = resource_path(self.SETTINGS_FILE)
        self.settings: dict[str, Any] = {}
        self.load_settings()

    def load_settings(self) -> None:
        """Load settings from disk, falling back to defaults on any error."""
        if not self.settings_file.exists():
            self.settings = self._get_default_settings()
            return
        try:
            with self.settings_file.open("r", encoding="utf-8") as f:
                self.settings = json.load(f)
        except Exception as exc:
            _logger.error("Failed to load settings", error=str(exc))
            self.settings = self._get_default_settings()

    def save_settings(self) -> None:
        """Persist the current settings dict to disk."""
        try:
            with self.settings_file.open("w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            _logger.error("Failed to save settings", error=str(exc))

    def _get_default_settings(self) -> dict[str, Any]:
        """Return the factory-default settings structure.

        :returns: Nested dict with ``connection``, ``ui``, and ``presets`` keys.
        """
        return {
            "connection": {
                "last_ip": "",
                "last_user": "",
                "last_simple_format": False,
            },
            "ui": {
                "window_geometry": "",
                "window_state": "",
                "last_test_mode": TestMode.HAPPY,
                "last_json_type": "normal",
            },
            "presets": {
                "last_preset": "",
                "last_endpoint": "",
                "last_json_file": "(none)",
            },
        }

    # ── Connection ────────────────────────────────────────────────────────────

    def get_last_ip(self) -> str:
        """Return the last-used device IP address.

        :returns: IP string, or ``""`` if not set.
        """
        return self.settings.get("connection", {}).get("last_ip", "")

    def set_last_ip(self, ip: str) -> None:
        """Persist the device IP address.

        :param ip: IP address string to store.
        """
        self.settings.setdefault("connection", {})["last_ip"] = ip

    def get_last_user(self) -> str:
        """Return the last-used authentication username.

        :returns: Username string, or ``""`` if not set.
        """
        return self.settings.get("connection", {}).get("last_user", "")

    def set_last_user(self, user: str) -> None:
        """Persist the authentication username.

        :param user: Username string to store.
        """
        self.settings.setdefault("connection", {})["last_user"] = user

    def get_last_simple_format(self) -> bool:
        """Return whether the simple response format was last selected.

        :returns: ``True`` if simple format was active, ``False`` otherwise.
        """
        return self.settings.get("connection", {}).get("last_simple_format", False)

    def set_last_simple_format(self, simple: bool) -> None:
        """Persist the simple response format toggle state.

        :param simple: ``True`` to enable simple format.
        """
        self.settings.setdefault("connection", {})["last_simple_format"] = simple

    # ── UI ────────────────────────────────────────────────────────────────────

    def get_window_geometry(self) -> str:
        """Return the saved window geometry as a hex string.

        :returns: Hex-encoded geometry bytes, or ``""`` if not set.
        """
        return self.settings.get("ui", {}).get("window_geometry", "")

    def set_window_geometry(self, geometry: str) -> None:
        """Persist the window geometry.

        :param geometry: Hex-encoded geometry bytes from ``QWidget.saveGeometry()``.
        """
        self.settings.setdefault("ui", {})["window_geometry"] = geometry

    def get_window_state(self) -> str:
        """Return the saved window state as a hex string.

        :returns: Hex-encoded state bytes, or ``""`` if not set.
        """
        return self.settings.get("ui", {}).get("window_state", "")

    def set_window_state(self, state: str) -> None:
        """Persist the window state.

        :param state: Hex-encoded state bytes from ``QMainWindow.saveState()``.
        """
        self.settings.setdefault("ui", {})["window_state"] = state

    def get_last_test_mode(self) -> str:
        """Return the last-selected test mode.

        :returns: ``"happy"`` or ``"unhappy"`` (default ``"happy"``).
        """
        return self.settings.get("ui", {}).get("last_test_mode", TestMode.HAPPY)

    def set_last_test_mode(self, mode: str) -> None:
        """Persist the selected test mode.

        :param mode: ``"happy"`` or ``"unhappy"``.
        """
        self.settings.setdefault("ui", {})["last_test_mode"] = mode

    def get_last_json_type(self) -> str:
        """Return the last-selected JSON payload type.

        :returns: Payload type string (default ``"normal"``).
        """
        return self.settings.get("ui", {}).get("last_json_type", "normal")

    def set_last_json_type(self, json_type: str) -> None:
        """Persist the selected JSON payload type.

        :param json_type: One of ``"normal"``, ``"google"``, or ``"rpc"``.
        """
        self.settings.setdefault("ui", {})["last_json_type"] = json_type

    # ── Presets ───────────────────────────────────────────────────────────────

    def get_last_preset(self) -> str:
        """Return the last-selected preset name.

        :returns: Preset name string, or ``""`` if not set.
        """
        return self.settings.get("presets", {}).get("last_preset", "")

    def set_last_preset(self, preset: str) -> None:
        """Persist the selected preset name.

        :param preset: Preset name string to store.
        """
        self.settings.setdefault("presets", {})["last_preset"] = preset

    def get_last_endpoint(self) -> str:
        """Return the last-selected API endpoint.

        :returns: Endpoint path string, or ``""`` if not set.
        """
        return self.settings.get("presets", {}).get("last_endpoint", "")

    def set_last_endpoint(self, endpoint: str) -> None:
        """Persist the selected API endpoint.

        :param endpoint: Endpoint path string to store.
        """
        self.settings.setdefault("presets", {})["last_endpoint"] = endpoint

    def get_last_json_file(self) -> str:
        """Return the last-selected JSON file path.

        :returns: Relative file path string, or ``"(none)"`` if not set.
        """
        return self.settings.get("presets", {}).get("last_json_file", "(none)")

    def set_last_json_file(self, json_file: str) -> None:
        """Persist the selected JSON file path.

        :param json_file: Relative path string to store.
        """
        self.settings.setdefault("presets", {})["last_json_file"] = json_file

