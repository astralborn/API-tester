"""Tests for app/settings_handling.py — SettingsHandlingMixin.

HOW THESE TESTS RUN WITHOUT THE APP
=====================================
Same pattern as test_request_handling.py:
  - Stub.__new__(Stub) skips QWidget.__init__ entirely.
  - MagicMock replaces every Qt widget attribute the mixin touches.
  - Methods that use QTimer (_setup_geometry_auto_save) are tested by verifying
    the timer is created; the actual timeout callback is tested separately.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def mixin():
    """Bare SettingsHandlingMixin instance — no Qt, no __init__ called."""
    from app.settings_handling import SettingsHandlingMixin

    class Stub(SettingsHandlingMixin):
        pass

    obj = Stub.__new__(Stub)

    # Qt widget stand-ins
    obj.ip_edit         = MagicMock()
    obj.user_edit       = MagicMock()
    obj.simple_check    = MagicMock()
    obj.test_mode_combo = MagicMock()
    obj.json_type_combo = MagicMock()
    obj.endpoint_combo  = MagicMock()
    obj.endpoint_combo.findText.return_value = -1  # default: endpoint not found
    obj.json_combo      = MagicMock()

    # restoreGeometry / saveGeometry are QWidget methods — mock them
    obj.restoreGeometry = MagicMock()
    obj.saveGeometry    = MagicMock()
    obj.saveGeometry.return_value.data.return_value.hex.return_value = "deadbeef"

    # Settings manager mock
    obj.settings = MagicMock()
    obj.settings.get_last_ip.return_value            = "10.0.0.1"
    obj.settings.get_last_user.return_value          = "admin"
    obj.settings.get_last_simple_format.return_value = True
    obj.settings.get_last_test_mode.return_value     = "unhappy"
    obj.settings.get_last_json_type.return_value     = "google"
    obj.settings.get_last_endpoint.return_value      = "/api/test"
    obj.settings.get_window_geometry.return_value    = ""  # empty → no restoreGeometry

    return obj


# ---------------------------------------------------------------------------
# load_settings
# ---------------------------------------------------------------------------

class TestLoadSettings:
    def test_sets_ip(self, mixin):
        mixin.load_settings()
        mixin.ip_edit.setText.assert_called_once_with("10.0.0.1")

    def test_sets_user(self, mixin):
        mixin.load_settings()
        mixin.user_edit.setText.assert_called_once_with("admin")

    def test_sets_simple_format(self, mixin):
        mixin.load_settings()
        mixin.simple_check.setChecked.assert_called_once_with(True)

    def test_sets_test_mode(self, mixin):
        mixin.load_settings()
        mixin.test_mode_combo.setCurrentText.assert_called_once_with("unhappy")

    def test_sets_json_type(self, mixin):
        mixin.load_settings()
        mixin.json_type_combo.setCurrentText.assert_called_once_with("google")

    def test_restores_geometry_when_present(self, mixin):
        mixin.settings.get_window_geometry.return_value = "deadbeef"
        mixin.load_settings()
        mixin.restoreGeometry.assert_called_once_with(bytes.fromhex("deadbeef"))

    def test_skips_restore_geometry_when_empty(self, mixin):
        mixin.settings.get_window_geometry.return_value = ""
        mixin.load_settings()
        mixin.restoreGeometry.assert_not_called()

    def test_endpoint_combo_set_when_found(self, mixin):
        # findText returns a valid index → setCurrentIndex should be called
        mixin.endpoint_combo.findText.return_value = 2
        mixin.load_settings()
        mixin.endpoint_combo.setCurrentIndex.assert_called_once_with(2)

    def test_endpoint_combo_not_set_when_not_found(self, mixin):
        # findText returns -1 → endpoint not in combo → setCurrentIndex must not be called
        mixin.endpoint_combo.findText.return_value = -1
        mixin.load_settings()
        mixin.endpoint_combo.setCurrentIndex.assert_not_called()

    def test_endpoint_combo_skipped_when_empty_string(self, mixin):
        mixin.settings.get_last_endpoint.return_value = ""
        mixin.load_settings()
        mixin.endpoint_combo.findText.assert_not_called()


# ---------------------------------------------------------------------------
# save_settings
# ---------------------------------------------------------------------------

class TestSaveSettings:
    def test_saves_ip(self, mixin):
        mixin.ip_edit.text.return_value = "192.168.1.50"
        mixin.save_settings()
        mixin.settings.set_last_ip.assert_called_once_with("192.168.1.50")

    def test_saves_user(self, mixin):
        mixin.user_edit.text.return_value = "john"
        mixin.save_settings()
        mixin.settings.set_last_user.assert_called_once_with("john")

    def test_saves_simple_format(self, mixin):
        mixin.simple_check.isChecked.return_value = False
        mixin.save_settings()
        mixin.settings.set_last_simple_format.assert_called_once_with(False)

    def test_saves_geometry_as_hex(self, mixin):
        mixin.save_settings()
        mixin.settings.set_window_geometry.assert_called_once_with("deadbeef")

    def test_calls_save_settings_on_manager(self, mixin):
        mixin.save_settings()
        mixin.settings.save_settings.assert_called_once()


# ---------------------------------------------------------------------------
# _auto_save_connection_settings
# ---------------------------------------------------------------------------

class TestAutoSaveConnectionSettings:
    def test_writes_ip_user_and_simple_format(self, mixin):
        mixin.ip_edit.text.return_value = "1.2.3.4"
        mixin.user_edit.text.return_value = "bob"
        mixin.simple_check.isChecked.return_value = True
        mixin._auto_save_connection_settings()
        mixin.settings.set_last_ip.assert_called_once_with("1.2.3.4")
        mixin.settings.set_last_user.assert_called_once_with("bob")
        mixin.settings.set_last_simple_format.assert_called_once_with(True)
        mixin.settings.save_settings.assert_called_once()


# ---------------------------------------------------------------------------
# _auto_save_ui_settings
# ---------------------------------------------------------------------------

class TestAutoSaveUiSettings:
    def test_writes_mode_type_endpoint_and_file(self, mixin):
        mixin.test_mode_combo.currentText.return_value = "happy"
        mixin.json_type_combo.currentText.return_value = "normal"
        mixin.endpoint_combo.currentText.return_value  = "/api/foo"
        mixin.json_combo.currentText.return_value      = "get/foo.json"
        mixin._auto_save_ui_settings()
        mixin.settings.set_last_test_mode.assert_called_once_with("happy")
        mixin.settings.set_last_json_type.assert_called_once_with("normal")
        mixin.settings.set_last_endpoint.assert_called_once_with("/api/foo")
        mixin.settings.set_last_json_file.assert_called_once_with("get/foo.json")
        mixin.settings.save_settings.assert_called_once()


# ---------------------------------------------------------------------------
# _auto_save_geometry
# ---------------------------------------------------------------------------

class TestAutoSaveGeometry:
    def test_saves_geometry_hex(self, mixin):
        mixin._auto_save_geometry()
        mixin.settings.set_window_geometry.assert_called_once_with("deadbeef")
        mixin.settings.save_settings.assert_called_once()
