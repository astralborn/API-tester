"""Widget-level integration tests for ApiTestApp.

These tests create a real (headless) QApplication + ApiTestApp instance,
wiring in mock managers so no real HTTP, disk I/O, or Qt-loop is needed.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest


# ---------------------------------------------------------------------------
# Fixture — fully wired app widget
# ---------------------------------------------------------------------------

@pytest.fixture()
def app_widget(qapp, mock_preset_manager, mock_request_manager, mock_settings_manager):
    """Return an ApiTestApp instance with all managers mocked out."""
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
# Startup / UI construction
# ---------------------------------------------------------------------------

class TestStartup:
    def test_window_title(self, app_widget):
        assert "API Test Tool" in app_widget.windowTitle()

    def test_has_ip_edit(self, app_widget):
        assert hasattr(app_widget, "ip_edit")

    def test_has_user_edit(self, app_widget):
        assert hasattr(app_widget, "user_edit")

    def test_has_pass_edit(self, app_widget):
        assert hasattr(app_widget, "pass_edit")

    def test_has_response_widget(self, app_widget):
        assert hasattr(app_widget, "response")

    def test_has_status_label(self, app_widget):
        assert hasattr(app_widget, "status")

    def test_cancel_button_initially_disabled(self, app_widget):
        assert not app_widget.btn_cancel.isEnabled()

    def test_initial_active_requests_empty(self, app_widget):
        assert app_widget.active_requests == []


# ---------------------------------------------------------------------------
# send_request validation (no real HTTP)
# ---------------------------------------------------------------------------

class TestSendRequestValidation:
    def test_warns_when_no_ip(self, app_widget, qtbot):
        app_widget.ip_edit.setText("")
        with patch("app.request_handling.QMessageBox.warning") as mock_warn:
            app_widget.send_request()
            mock_warn.assert_called_once()
            assert "IP" in mock_warn.call_args[0][2]

    def test_warns_when_invalid_ip(self, app_widget):
        app_widget.ip_edit.setText("bad-ip")
        with patch("app.request_handling.QMessageBox.warning") as mock_warn:
            app_widget.send_request()
            mock_warn.assert_called_once()
            assert "Invalid" in mock_warn.call_args[0][2]

    def test_warns_when_no_username(self, app_widget):
        app_widget.ip_edit.setText("192.168.1.1")
        app_widget.user_edit.setText("")
        with patch("app.request_handling.QMessageBox.warning") as mock_warn:
            app_widget.send_request()
            mock_warn.assert_called_once()
            assert "Username" in mock_warn.call_args[0][2]

    def test_sends_when_ip_and_user_provided(self, app_widget, mock_request_manager):
        app_widget.ip_edit.setText("192.168.1.100")
        app_widget.user_edit.setText("admin")
        app_widget.pass_edit.setText("pass")

        app_widget.send_request()

        mock_request_manager.send_request_async.assert_called_once()

    def test_tracks_worker_after_send(self, app_widget, mock_request_manager):
        app_widget.ip_edit.setText("10.0.0.1")
        app_widget.user_edit.setText("admin")

        app_widget.send_request()

        assert len(app_widget.active_requests) == 1

    def test_cancel_button_enabled_after_send(self, app_widget, mock_request_manager):
        app_widget.ip_edit.setText("10.0.0.1")
        app_widget.user_edit.setText("admin")

        app_widget.send_request()

        assert app_widget.btn_cancel.isEnabled()


# ---------------------------------------------------------------------------
# cancel_all_requests
# ---------------------------------------------------------------------------

class TestCancelRequests:
    def test_cancel_clears_active_requests(self, app_widget, mock_request_manager):
        # Seed one worker
        app_widget.ip_edit.setText("10.0.0.1")
        app_widget.user_edit.setText("admin")
        app_widget.send_request()

        app_widget.cancel_all_requests()

        assert app_widget.active_requests == []

    def test_cancel_disables_cancel_button(self, app_widget, mock_request_manager):
        app_widget.ip_edit.setText("10.0.0.1")
        app_widget.user_edit.setText("admin")
        app_widget.send_request()

        app_widget.cancel_all_requests()

        assert not app_widget.btn_cancel.isEnabled()

    def test_cancel_with_no_requests_is_noop(self, app_widget):
        # Should not raise
        app_widget.cancel_all_requests()


# ---------------------------------------------------------------------------
# load_preset
# ---------------------------------------------------------------------------

class TestLoadPreset:
    def test_warns_when_no_preset_selected(self, app_widget):
        app_widget.preset_combo.clear()
        with patch("app.preset_handling.QMessageBox.warning") as mock_warn:
            app_widget.load_preset()
            mock_warn.assert_called_once()

    def test_loads_endpoint_from_preset(self, app_widget, mock_preset_manager):
        from config.constants import API_ENDPOINTS

        preset = {
            "name": "P1",
            "endpoint": API_ENDPOINTS[0],
            "json_file": "(none)",
            "json_type": "normal",
        }
        mock_preset_manager.get_by_name.return_value = preset
        app_widget.preset_combo.addItem("P1")
        app_widget.preset_combo.setCurrentText("P1")

        app_widget.load_preset()

        assert app_widget.endpoint_combo.currentText() == API_ENDPOINTS[0]

    def test_warns_when_preset_not_found(self, app_widget, mock_preset_manager):
        mock_preset_manager.get_by_name.return_value = None
        app_widget.preset_combo.addItem("Ghost")
        app_widget.preset_combo.setCurrentText("Ghost")

        with patch("app.preset_handling.QMessageBox.warning") as mock_warn:
            app_widget.load_preset()
            mock_warn.assert_called_once()


# ---------------------------------------------------------------------------
# settings round-trip
# ---------------------------------------------------------------------------

class TestSettingsRoundTrip:
    def test_save_settings_calls_manager(self, app_widget, mock_settings_manager):
        app_widget.ip_edit.setText("1.2.3.4")
        app_widget.save_settings()
        mock_settings_manager.set_last_ip.assert_called_with("1.2.3.4")
        mock_settings_manager.save_settings.assert_called()

    def test_load_settings_reads_ip(self, app_widget, mock_settings_manager):
        mock_settings_manager.get_last_ip.return_value = "5.6.7.8"
        app_widget.load_settings()
        assert app_widget.ip_edit.text() == "5.6.7.8"

    def test_load_settings_reads_test_mode(self, app_widget, mock_settings_manager):
        mock_settings_manager.get_last_test_mode.return_value = "unhappy"
        app_widget.load_settings()
        assert app_widget.test_mode_combo.currentText() == "unhappy"


# ---------------------------------------------------------------------------
# clear_response
# ---------------------------------------------------------------------------

class TestClearResponse:
    def test_clears_response_widget(self, app_widget, qtbot):
        app_widget.response.insertPlainText("some text")
        app_widget.clear_response()
        assert app_widget.response.toPlainText() == ""


# ---------------------------------------------------------------------------
# ApiTestApp — construction via DIContainer
# ---------------------------------------------------------------------------

class TestContainerConstruction:
    def test_managers_resolved_from_container(
        self, qapp, mock_preset_manager, mock_request_manager, mock_settings_manager
    ):
        """When a DIContainer is passed, managers must be resolved from it (lines 42-45)."""
        from config.di_container import DIContainer
        mock_logger = MagicMock()

        container = MagicMock(spec=DIContainer)
        container.get.side_effect = lambda name: {
            "preset_manager":  mock_preset_manager,
            "request_manager": mock_request_manager,
            "settings_manager": mock_settings_manager,
        }[name]

        with (
            patch("app.__init__.get_logger", return_value=mock_logger),
            patch("app.__init__.resource_path", return_value=MagicMock()),
        ):
            from app import ApiTestApp
            widget = ApiTestApp(container=container)

        # All three services must have been fetched from the container
        assert widget.presets  is mock_preset_manager
        assert widget.requests is mock_request_manager
        assert widget.settings is mock_settings_manager
        widget.close()


# ---------------------------------------------------------------------------
# send_request — exception path (lines 65-68 of request_handling.py)
# ---------------------------------------------------------------------------

class TestSendRequestExceptionPath:
    def test_exception_during_send_updates_status(self, app_widget):
        """If send_request_async raises, status bar must show 'failed'."""
        app_widget.ip_edit.setText("10.0.0.1")
        app_widget.user_edit.setText("admin")
        app_widget.requests.send_request_async.side_effect = RuntimeError("network down")

        with patch("app.request_handling.QMessageBox.critical"):
            app_widget.send_request()

        assert "failed" in app_widget.status.text().lower()

    def test_exception_during_send_shows_critical_dialog(self, app_widget):
        app_widget.ip_edit.setText("10.0.0.1")
        app_widget.user_edit.setText("admin")
        app_widget.requests.send_request_async.side_effect = RuntimeError("network down")

        with patch("app.request_handling.QMessageBox.critical") as mock_crit:
            app_widget.send_request()
            mock_crit.assert_called_once()

    def test_on_response_callback_updates_status(self, app_widget, mock_request_manager):
        """Trigger the on_response inner callback to cover lines 47-49."""
        app_widget.ip_edit.setText("10.0.0.1")
        app_widget.user_edit.setText("admin")

        captured_callback = None

        def capture(*args, **kwargs):
            nonlocal captured_callback
            captured_callback = kwargs.get("callback") or args[7]
            return mock_request_manager.send_request_async.return_value

        mock_request_manager.send_request_async.side_effect = capture
        app_widget.send_request()

        # Now fire the callback as the worker would
        assert captured_callback is not None
        captured_callback('{"ok":1}', "MyPreset", "ok")

        assert "finished" in app_widget.status.text().lower()


