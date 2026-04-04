"""Tests for managers/settings.py — SettingsManager."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_manager(settings_file: Path):
    with patch("managers.settings.SettingsManager.SETTINGS_FILE", str(settings_file.name)):
        with patch("config.constants.resource_path", return_value=settings_file):
            from managers.settings import SettingsManager
            mgr = SettingsManager.__new__(SettingsManager)
            mgr.settings_file = settings_file
            mgr.settings = {}
            mgr.load_settings()
            return mgr


def _fresh(tmp_path: Path) -> "SettingsManager":  # noqa: F821
    """Create a SettingsManager backed by a temp file."""
    from managers.settings import SettingsManager
    mgr = SettingsManager.__new__(SettingsManager)
    mgr.settings_file = tmp_path / "settings.json"
    mgr.settings = mgr._get_default_settings()
    return mgr


# ---------------------------------------------------------------------------
# Default settings
# ---------------------------------------------------------------------------

class TestDefaultSettings:
    def test_default_ip_is_empty(self, tmp_path):
        mgr = _fresh(tmp_path)
        assert mgr.get_last_ip() == ""

    def test_default_user_is_empty(self, tmp_path):
        mgr = _fresh(tmp_path)
        assert mgr.get_last_user() == ""

    def test_default_simple_format_is_false(self, tmp_path):
        mgr = _fresh(tmp_path)
        assert mgr.get_last_simple_format() is False

    def test_default_test_mode_is_happy(self, tmp_path):
        mgr = _fresh(tmp_path)
        assert mgr.get_last_test_mode() == "happy"

    def test_default_json_type_is_normal(self, tmp_path):
        mgr = _fresh(tmp_path)
        assert mgr.get_last_json_type() == "normal"

    def test_default_json_file_is_none(self, tmp_path):
        mgr = _fresh(tmp_path)
        assert mgr.get_last_json_file() == "(none)"

    def test_default_geometry_is_empty(self, tmp_path):
        mgr = _fresh(tmp_path)
        assert mgr.get_window_geometry() == ""


# ---------------------------------------------------------------------------
# Setters / getters round-trip
# ---------------------------------------------------------------------------

class TestSettersAndGetters:
    def test_set_get_ip(self, tmp_path):
        mgr = _fresh(tmp_path)
        mgr.set_last_ip("10.0.0.1")
        assert mgr.get_last_ip() == "10.0.0.1"

    def test_set_get_user(self, tmp_path):
        mgr = _fresh(tmp_path)
        mgr.set_last_user("alice")
        assert mgr.get_last_user() == "alice"

    def test_set_get_simple_format_true(self, tmp_path):
        mgr = _fresh(tmp_path)
        mgr.set_last_simple_format(True)
        assert mgr.get_last_simple_format() is True

    def test_set_get_test_mode(self, tmp_path):
        mgr = _fresh(tmp_path)
        mgr.set_last_test_mode("unhappy")
        assert mgr.get_last_test_mode() == "unhappy"

    def test_set_get_json_type(self, tmp_path):
        mgr = _fresh(tmp_path)
        mgr.set_last_json_type("google")
        assert mgr.get_last_json_type() == "google"

    def test_set_get_endpoint(self, tmp_path):
        mgr = _fresh(tmp_path)
        mgr.set_last_endpoint("/api/call/GetSIPAccount")
        assert mgr.get_last_endpoint() == "/api/call/GetSIPAccount"

    def test_set_get_json_file(self, tmp_path):
        mgr = _fresh(tmp_path)
        mgr.set_last_json_file("get/normal_action/foo.json")
        assert mgr.get_last_json_file() == "get/normal_action/foo.json"

    def test_set_get_window_geometry(self, tmp_path):
        mgr = _fresh(tmp_path)
        mgr.set_window_geometry("deadbeef")
        assert mgr.get_window_geometry() == "deadbeef"

    def test_set_get_window_state(self, tmp_path):
        mgr = _fresh(tmp_path)
        mgr.set_window_state("maximized")
        assert mgr.get_window_state() == "maximized"

    def test_set_get_preset(self, tmp_path):
        mgr = _fresh(tmp_path)
        mgr.set_last_preset("My Preset")
        assert mgr.get_last_preset() == "My Preset"


# ---------------------------------------------------------------------------
# Persistence (save → load)
# ---------------------------------------------------------------------------

class TestPersistence:
    def test_save_and_reload(self, tmp_path):
        from managers.settings import SettingsManager

        mgr = _fresh(tmp_path)
        mgr.set_last_ip("192.168.1.42")
        mgr.set_last_user("bob")
        mgr.save_settings()

        mgr2 = SettingsManager.__new__(SettingsManager)
        mgr2.settings_file = mgr.settings_file
        mgr2.settings = {}
        mgr2.load_settings()

        assert mgr2.get_last_ip() == "192.168.1.42"
        assert mgr2.get_last_user() == "bob"

    def test_load_missing_file_uses_defaults(self, tmp_path):
        from managers.settings import SettingsManager

        mgr = SettingsManager.__new__(SettingsManager)
        mgr.settings_file = tmp_path / "nonexistent.json"
        mgr.settings = {}
        mgr.load_settings()

        assert mgr.get_last_ip() == ""
        assert mgr.get_last_test_mode() == "happy"

    def test_load_corrupt_file_uses_defaults(self, tmp_path):
        from managers.settings import SettingsManager

        f = tmp_path / "bad.json"
        f.write_text("NOT_JSON", encoding="utf-8")
        mgr = SettingsManager.__new__(SettingsManager)
        mgr.settings_file = f
        mgr.settings = {}
        mgr.load_settings()

        assert mgr.get_last_ip() == ""

    def test_save_fails_silently_on_bad_path(self, tmp_path):
        from managers.settings import SettingsManager

        mgr = _fresh(tmp_path)
        # Point file at a directory (cannot be written)
        bad = tmp_path / "dir"
        bad.mkdir()
        mgr.settings_file = bad
        mgr.save_settings()  # must not raise

    def test_real_init_via_resource_path(self, tmp_path):
        """Call SettingsManager.__init__ for real to cover lines 18-20."""
        from managers.settings import SettingsManager
        with patch("managers.settings.resource_path", return_value=tmp_path / "s.json"):
            mgr = SettingsManager()
        assert mgr.get_last_ip() == ""

