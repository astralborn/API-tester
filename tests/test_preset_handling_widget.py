"""Widget-level tests for app/preset_handling.py — methods that need a real QWidget.

These tests use the app_widget fixture (real QApplication + ApiTestApp with mock
managers) to exercise the Qt-interaction methods of PresetHandlingMixin that cannot
be tested with __new__ alone: update_presets_list, on_preset_changed, save_preset,
load_preset.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixture — re-use the one from conftest via app_widget
# ---------------------------------------------------------------------------

@pytest.fixture()
def app_widget(qapp, mock_preset_manager, mock_request_manager, mock_settings_manager):
    mock_logger = MagicMock()
    with (
        patch("app.__init__.get_logger", return_value=mock_logger),
        patch("app.__init__.resource_path", return_value=MagicMock()),
    ):
        from app import ApiTestApp
        widget = ApiTestApp(
            preset_manager=mock_preset_manager,
            request_manager=mock_request_manager,
            settings_manager=mock_settings_manager,
        )
    yield widget
    widget.close()


# ---------------------------------------------------------------------------
# update_presets_list  (lines 25-37)
# ---------------------------------------------------------------------------

class TestUpdatePresetsList:
    def test_populates_combo_with_matching_presets(self, app_widget, mock_preset_manager):
        """Matching presets are added to preset_combo."""
        mock_preset_manager.presets = [
            {"name": "GetContacts Happy", "json_file": "get/normal_action/foo.json",
             "simple_format": False, "json_type": "normal"},
        ]
        app_widget.test_mode_combo.setCurrentText("happy")
        app_widget.preset_search.setText("")
        app_widget.update_presets_list()
        assert app_widget.preset_combo.findText("GetContacts Happy") >= 0

    def test_excludes_non_matching_presets(self, app_widget, mock_preset_manager):
        """Unhappy presets are excluded in happy mode."""
        mock_preset_manager.presets = [
            {"name": "GetContacts Unhappy", "json_file": "get/unhappy/foo.json",
             "simple_format": False, "json_type": "normal"},
        ]
        app_widget.test_mode_combo.setCurrentText("happy")
        app_widget.preset_search.setText("")
        app_widget.update_presets_list()
        assert app_widget.preset_combo.count() == 0

    def test_empty_preset_list_leaves_combo_empty(self, app_widget, mock_preset_manager):
        mock_preset_manager.presets = []
        app_widget.update_presets_list()
        assert app_widget.preset_combo.count() == 0


# ---------------------------------------------------------------------------
# on_preset_changed  (lines 39-48)
# ---------------------------------------------------------------------------

class TestOnPresetChanged:
    def test_sets_json_combo_from_preset(self, app_widget, mock_preset_manager):
        """When a valid preset is selected, json_combo reflects its json_file."""
        mock_preset_manager.get_by_name.return_value = {
            "name": "P1",
            "endpoint": "/api/test",
            "json_file": "get/normal_action/foo.json",
            "json_type": "normal",
        }
        app_widget.on_preset_changed("P1")
        assert app_widget.json_combo.currentText() == "get/normal_action/foo.json"

    def test_unknown_preset_is_noop(self, app_widget, mock_preset_manager):
        """If get_by_name returns None, json_combo is left unchanged."""
        mock_preset_manager.get_by_name.return_value = None
        before = app_widget.json_combo.currentText()
        app_widget.on_preset_changed("Ghost")
        assert app_widget.json_combo.currentText() == before

    def test_preset_with_none_json_file_adds_only_none(self, app_widget, mock_preset_manager):
        """A preset with json_file == '(none)' should not add an extra item."""
        mock_preset_manager.get_by_name.return_value = {
            "name": "P2",
            "endpoint": "/api/test",
            "json_file": "(none)",
            "json_type": "normal",
        }
        app_widget.on_preset_changed("P2")
        assert app_widget.json_combo.count() == 1
        assert app_widget.json_combo.itemText(0) == "(none)"


# ---------------------------------------------------------------------------
# save_preset  (lines 50-64)
# ---------------------------------------------------------------------------

class TestSavePreset:
    def test_save_preset_cancelled_when_dialog_rejected(self, app_widget, mock_preset_manager):
        """If user cancels QInputDialog, add_preset must NOT be called."""
        with patch("app.preset_handling.QInputDialog.getText", return_value=("", False)):
            app_widget.save_preset()
        mock_preset_manager.add_preset.assert_not_called()

    def test_save_preset_cancelled_when_name_empty(self, app_widget, mock_preset_manager):
        """If user submits an empty name, add_preset must NOT be called."""
        with patch("app.preset_handling.QInputDialog.getText", return_value=("", True)):
            app_widget.save_preset()
        mock_preset_manager.add_preset.assert_not_called()

    def test_save_preset_calls_add_preset_with_name(self, app_widget, mock_preset_manager):
        """Happy path: valid name → add_preset called with the right name."""
        with patch("app.preset_handling.QInputDialog.getText", return_value=("MyPreset", True)):
            app_widget.save_preset()
        mock_preset_manager.add_preset.assert_called_once()
        saved = mock_preset_manager.add_preset.call_args[0][0]
        assert saved["name"] == "MyPreset"


# ---------------------------------------------------------------------------
# run_multiple  (lines 88-157)
# ---------------------------------------------------------------------------

class TestRunMultiple:
    def test_warns_when_no_presets_available(self, app_widget):
        """preset_combo empty → QMessageBox.warning, nothing else."""
        app_widget.preset_combo.clear()
        with patch("app.preset_handling.QMessageBox.warning") as mock_warn:
            app_widget.run_multiple()
            mock_warn.assert_called_once()

    def test_does_nothing_when_dialog_cancelled(self, app_widget, mock_preset_manager):
        """User cancels MultiSelectDialog → send_request_async never called."""
        mock_preset_manager.presets = [
            {"name": "P1", "json_file": "get/normal_action/foo.json",
             "simple_format": False, "json_type": "normal"},
        ]
        app_widget.update_presets_list()
        with patch("app.preset_handling.MultiSelectDialog") as MockDlg:
            MockDlg.return_value.exec.return_value = False
            app_widget.run_multiple()
        mock_preset_manager.send_request_async = MagicMock()
        app_widget.requests.send_request_async.assert_not_called()

    def test_warns_when_no_ip(self, app_widget, mock_preset_manager):
        """Dialog accepted but IP empty → warning."""
        mock_preset_manager.presets = [
            {"name": "P1", "json_file": "get/normal_action/foo.json",
             "simple_format": False, "json_type": "normal"},
        ]
        app_widget.update_presets_list()
        app_widget.ip_edit.setText("")
        with patch("app.preset_handling.MultiSelectDialog") as MockDlg:
            MockDlg.return_value.exec.return_value = True
            MockDlg.return_value.selected = ["P1"]
            with patch("app.preset_handling.QMessageBox.warning") as mock_warn:
                app_widget.run_multiple()
                mock_warn.assert_called_once()

    def test_warns_when_invalid_ip(self, app_widget, mock_preset_manager):
        """Dialog accepted but IP invalid → warning."""
        mock_preset_manager.presets = [
            {"name": "P1", "json_file": "get/normal_action/foo.json",
             "simple_format": False, "json_type": "normal"},
        ]
        app_widget.update_presets_list()
        app_widget.ip_edit.setText("not-an-ip")
        with patch("app.preset_handling.MultiSelectDialog") as MockDlg:
            MockDlg.return_value.exec.return_value = True
            MockDlg.return_value.selected = ["P1"]
            with patch("app.preset_handling.QMessageBox.warning") as mock_warn:
                app_widget.run_multiple()
                mock_warn.assert_called_once()

    def test_warns_when_no_username(self, app_widget, mock_preset_manager):
        """Dialog accepted, valid IP, but no username → warning."""
        mock_preset_manager.presets = [
            {"name": "P1", "json_file": "get/normal_action/foo.json",
             "simple_format": False, "json_type": "normal"},
        ]
        app_widget.update_presets_list()
        app_widget.ip_edit.setText("10.0.0.1")
        app_widget.user_edit.setText("")
        with patch("app.preset_handling.MultiSelectDialog") as MockDlg:
            MockDlg.return_value.exec.return_value = True
            MockDlg.return_value.selected = ["P1"]
            with patch("app.preset_handling.QMessageBox.warning") as mock_warn:
                app_widget.run_multiple()
                mock_warn.assert_called_once()

    def test_happy_path_calls_send_request_async(self, app_widget, mock_preset_manager):
        """Full happy path: valid IP, user, preset → send_request_async called."""
        preset = {"name": "P1", "endpoint": "/api/test",
                  "json_file": "get/normal_action/foo.json",
                  "simple_format": False, "json_type": "normal"}
        mock_preset_manager.presets = [preset]
        mock_preset_manager.get_by_name.return_value = preset
        app_widget.update_presets_list()
        app_widget.ip_edit.setText("10.0.0.1")
        app_widget.user_edit.setText("admin")

        with patch("app.preset_handling.MultiSelectDialog") as MockDlg:
            MockDlg.return_value.exec.return_value = True
            MockDlg.return_value.selected = ["P1"]
            app_widget.run_multiple()

        app_widget.requests.send_request_async.assert_called_once()

    def test_log_file_error_shows_critical(self, app_widget, mock_preset_manager):
        """If start_new_log raises → QMessageBox.critical shown."""
        mock_preset_manager.presets = [
            {"name": "P1", "json_file": "get/normal_action/foo.json",
             "simple_format": False, "json_type": "normal"},
        ]
        app_widget.update_presets_list()
        app_widget.ip_edit.setText("10.0.0.1")
        app_widget.user_edit.setText("admin")
        app_widget.requests.start_new_log.side_effect = OSError("disk full")

        with patch("app.preset_handling.MultiSelectDialog") as MockDlg:
            MockDlg.return_value.exec.return_value = True
            MockDlg.return_value.selected = ["P1"]
            with patch("app.preset_handling.QMessageBox.critical") as mock_crit:
                app_widget.run_multiple()
                mock_crit.assert_called_once()

    def test_skips_invalid_preset_and_continues(self, app_widget, mock_preset_manager, qtbot):
        """run_next: preset not found → status shows 'Skipping', moves to next via QTimer."""
        mock_preset_manager.presets = [
            {"name": "Ghost", "json_file": "get/normal_action/foo.json",
             "simple_format": False, "json_type": "normal"},
        ]
        app_widget.update_presets_list()
        app_widget.ip_edit.setText("10.0.0.1")
        app_widget.user_edit.setText("admin")
        # get_by_name returns None → preset is "invalid"
        mock_preset_manager.get_by_name.return_value = None

        with patch("app.preset_handling.MultiSelectDialog") as MockDlg:
            MockDlg.return_value.exec.return_value = True
            MockDlg.return_value.selected = ["Ghost"]
            app_widget.run_multiple()

        # Allow QTimer.singleShot(0, run_next) to fire
        qtbot.wait(50)
        assert "Skipping" in app_widget.status.text() or "finished" in app_widget.status.text()

    def test_send_exception_in_run_next_continues(self, app_widget, mock_preset_manager, qtbot):
        """run_next: send_request_async raises → status shows error, moves on via QTimer."""
        preset = {"name": "P1", "endpoint": "/api/test",
                  "json_file": "get/normal_action/foo.json",
                  "simple_format": False, "json_type": "normal"}
        mock_preset_manager.presets = [preset]
        mock_preset_manager.get_by_name.return_value = preset
        app_widget.update_presets_list()
        app_widget.ip_edit.setText("10.0.0.1")
        app_widget.user_edit.setText("admin")
        app_widget.requests.send_request_async.side_effect = RuntimeError("bang")

        with patch("app.preset_handling.MultiSelectDialog") as MockDlg:
            MockDlg.return_value.exec.return_value = True
            MockDlg.return_value.selected = ["P1"]
            app_widget.run_multiple()

        qtbot.wait(50)
        assert "Failed" in app_widget.status.text() or "finished" in app_widget.status.text()

    def test_all_presets_finished_updates_status(self, app_widget, mock_preset_manager, qtbot):
        """After all presets run, status shows 'All presets finished'."""
        preset = {"name": "P1", "endpoint": "/api/test",
                  "json_file": "get/normal_action/foo.json",
                  "simple_format": False, "json_type": "normal"}
        mock_preset_manager.presets = [preset]
        mock_preset_manager.get_by_name.return_value = preset
        app_widget.update_presets_list()
        app_widget.ip_edit.setText("10.0.0.1")
        app_widget.user_edit.setText("admin")

        # Capture on_response callback and call it synchronously to trigger run_next → empty queue
        captured = {}

        def capture_callback(*args, **kwargs):
            captured["callback"] = kwargs.get("callback") or args[7]
            return app_widget.requests.send_request_async.return_value

        app_widget.requests.send_request_async.side_effect = capture_callback

        with patch("app.preset_handling.MultiSelectDialog") as MockDlg:
            MockDlg.return_value.exec.return_value = True
            MockDlg.return_value.selected = ["P1"]
            app_widget.run_multiple()

        # Fire the on_response callback — this triggers QTimer.singleShot(0, run_next)
        # with empty queue → "All presets finished"
        if captured.get("callback"):
            captured["callback"]("response", "P1", "ok")

        qtbot.wait(50)
        assert "finished" in app_widget.status.text().lower()


