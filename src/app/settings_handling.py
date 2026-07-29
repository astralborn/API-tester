"""Settings handling mixin for API Test Tool."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QCheckBox, QComboBox, QLineEdit, QWidget

if TYPE_CHECKING:
    from config.di_container import SettingsManagerProtocol

    class _SettingsHandlingProtocol(QWidget):
        """Typed view of the fully-assembled host class, for use in method stubs."""

        ip_edit: QLineEdit
        user_edit: QLineEdit
        pass_edit: QLineEdit
        simple_check: QCheckBox
        test_mode_combo: QComboBox
        json_type_combo: QComboBox
        endpoint_combo: QComboBox
        json_combo: QComboBox
        settings: SettingsManagerProtocol
        _connection_save_timer: QTimer
        _ui_save_timer: QTimer
else:
    _SettingsHandlingProtocol = object


class SettingsHandlingMixin(_SettingsHandlingProtocol):
    """Mixin that loads, saves, and auto-saves application settings."""

    def load_settings(self: _SettingsHandlingProtocol) -> None:
        """Restore all persisted settings into the UI widgets."""
        self.ip_edit.setText(self.settings.get_last_ip())
        self.user_edit.setText(self.settings.get_last_user())
        self.simple_check.setChecked(self.settings.get_last_simple_format())
        self.test_mode_combo.setCurrentText(self.settings.get_last_test_mode())
        self.json_type_combo.setCurrentText(self.settings.get_last_json_type())

        last_endpoint = self.settings.get_last_endpoint()
        if last_endpoint:
            index = self.endpoint_combo.findText(last_endpoint)
            if index >= 0:
                self.endpoint_combo.setCurrentIndex(index)

        geometry = self.settings.get_window_geometry()
        if geometry:
            self.restoreGeometry(bytes.fromhex(geometry))

    def save_settings(self: _SettingsHandlingProtocol) -> None:
        """Collect all current UI values and persist them to disk."""
        self.settings.set_last_ip(self.ip_edit.text())
        self.settings.set_last_user(self.user_edit.text())
        self.settings.set_last_simple_format(self.simple_check.isChecked())
        self.settings.set_last_test_mode(self.test_mode_combo.currentText())
        self.settings.set_last_json_type(self.json_type_combo.currentText())
        self.settings.set_last_endpoint(self.endpoint_combo.currentText())
        self.settings.set_last_json_file(self.json_combo.currentText())
        geometry = self.saveGeometry().data().hex()
        self.settings.set_window_geometry(geometry)
        self.settings.save_settings()

    def _auto_save_connection_settings(self: _SettingsHandlingProtocol) -> None:
        """Stage connection-related fields and schedule a debounced save."""
        self.settings.set_last_ip(self.ip_edit.text())
        self.settings.set_last_user(self.user_edit.text())
        self.settings.set_last_simple_format(self.simple_check.isChecked())
        self._connection_save_timer.start(500)

    def _auto_save_ui_settings(self: _SettingsHandlingProtocol) -> None:
        """Stage UI-state fields and schedule a debounced save."""
        self.settings.set_last_test_mode(self.test_mode_combo.currentText())
        self.settings.set_last_json_type(self.json_type_combo.currentText())
        self.settings.set_last_endpoint(self.endpoint_combo.currentText())
        self.settings.set_last_json_file(self.json_combo.currentText())
        self._ui_save_timer.start(500)

    def _setup_geometry_auto_save(self) -> None:
        """Create single-shot timers used to debounce all auto-saves."""
        self._geometry_timer = QTimer()
        self._geometry_timer.setSingleShot(True)
        self._geometry_timer.timeout.connect(self._auto_save_geometry)

        self._connection_save_timer = QTimer()
        self._connection_save_timer.setSingleShot(True)
        self._connection_save_timer.timeout.connect(self.settings.save_settings)

        self._ui_save_timer = QTimer()
        self._ui_save_timer.setSingleShot(True)
        self._ui_save_timer.timeout.connect(self.settings.save_settings)

    def _auto_save_geometry(self: _SettingsHandlingProtocol) -> None:
        """Write the current window geometry to settings."""
        geometry = self.saveGeometry().data().hex()
        self.settings.set_window_geometry(geometry)
        self.settings.save_settings()
