"""Preset handling mixin for API Test Tool."""
from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QWidget,
)

from app.dialogs import MultiSelectDialog

if TYPE_CHECKING:
    from config.di_container import PresetManagerProtocol, RequestManagerProtocol
    from config.logging_system import StructuredLogger
    from managers.requests_manager import RequestWorker

    class _PresetHandlingProtocol(QWidget):
        """Typed view of the fully-assembled host class, for use in method stubs."""

        ip_edit: QLineEdit
        user_edit: QLineEdit
        pass_edit: QLineEdit
        simple_check: QCheckBox
        preset_search: QLineEdit
        test_mode_combo: QComboBox
        preset_combo: QComboBox
        endpoint_combo: QComboBox
        json_combo: QComboBox
        json_type_combo: QComboBox
        status: QLabel
        presets: PresetManagerProtocol
        requests: RequestManagerProtocol
        logger: StructuredLogger
        current_request_count: int
        total_request_count: int

        # Cross-mixin and internal method stubs
        def _validate_ip(self, ip: str) -> bool: ...
        def _track_request(self, worker: RequestWorker) -> None: ...
        def _untrack_request(self, worker: RequestWorker) -> None: ...
        def _update_progress(self, completed: int, total: int) -> None: ...
        def display_response(self, text: str, preset_name: str, tag: str) -> None: ...
        def _preset_matches(self, preset: dict, mode: str, search: str) -> bool: ...
        def on_preset_changed(self, name: str) -> None: ...
        def update_presets_list(self) -> None: ...
else:
    _PresetHandlingProtocol = object


class PresetHandlingMixin(_PresetHandlingProtocol):  # type: ignore[misc]
    """Mixin that manages preset loading, saving, and batch execution."""

    def _preset_matches(self, preset: dict[str, Any], mode: str, search: str) -> bool:
        """Return True if *preset* matches the current mode and search string.

        :param preset: Preset dict to evaluate.
        :param mode: Either ``"happy"`` or ``"unhappy"``.
        :param search: Case-insensitive substring to match against the preset name.
        """
        name = preset.get("name", "")
        json_file = preset.get("json_file", "")
        if not json_file:
            return False
        is_unhappy = "/unhappy/" in json_file.replace("\\", "/").lower()
        if (mode == "happy" and is_unhappy) or (mode == "unhappy" and not is_unhappy):
            return False
        return search.lower() in name.lower()

    def update_presets_list(self: _PresetHandlingProtocol) -> None:  # type: ignore[misc]
        """Repopulate the preset and JSON-file combo boxes based on mode and search."""
        search = self.preset_search.text().lower()
        mode = self.test_mode_combo.currentText().lower()
        self.preset_combo.clear()
        self.json_combo.clear()
        self.json_combo.addItem("(none)")
        for preset in self.presets.presets:
            if self._preset_matches(preset, mode, search):
                self.preset_combo.addItem(preset["name"])
                self.json_combo.addItem(preset["json_file"])
        if self.preset_combo.count():
            self.preset_combo.setCurrentIndex(0)
            self.on_preset_changed(self.preset_combo.currentText())

    def on_preset_changed(self: _PresetHandlingProtocol, name: str) -> None:  # type: ignore[misc]
        """Sync the JSON-file combo box when the selected preset changes.

        :param name: Name of the newly selected preset.
        """
        preset = self.presets.get_by_name(name)
        if not preset:
            return
        self.json_combo.clear()
        self.json_combo.addItem("(none)")
        json_file = preset.get("json_file")
        if json_file and json_file != "(none)":
            self.json_combo.addItem(json_file)
            self.json_combo.setCurrentText(json_file)

    def save_preset(self: _PresetHandlingProtocol) -> None:  # type: ignore[misc]
        """Prompt the user for a name and persist the current request config as a preset."""
        name, ok = QInputDialog.getText(self, "Preset Name", "Enter preset name:")
        if not ok or not name:
            self.logger.log_user_action("save_preset_cancelled")
            return
        self.logger.log_preset_action("save_started", name)
        self.presets.add_preset({
            "name": name,
            "endpoint": self.endpoint_combo.currentText(),
            "json_file": self.json_combo.currentText(),
            "simple_format": self.simple_check.isChecked(),
            "json_type": self.json_type_combo.currentText(),
        })
        self.update_presets_list()
        self.logger.log_preset_action(
            "save_completed",
            name,
            endpoint=self.endpoint_combo.currentText(),
            json_file=self.json_combo.currentText(),
        )

    def load_preset(self: _PresetHandlingProtocol) -> None:  # type: ignore[misc]
        """Load the currently selected preset into the request UI fields."""
        name = self.preset_combo.currentText().strip()
        if not name:
            self.logger.log_user_action("load_preset_failed", reason="no_selection")
            QMessageBox.warning(self, "Error", "No preset selected")
            return
        self.logger.log_preset_action("load_started", name)
        preset = self.presets.get_by_name(name)
        if not preset:
            self.logger.log_preset_action("load_failed", name, reason="not_found")
            QMessageBox.warning(self, "Error", f"Preset '{name}' not found")
            return
        self.endpoint_combo.setCurrentText(preset["endpoint"])
        self.json_combo.setCurrentText(preset.get("json_file", "(none)"))
        self.json_type_combo.setCurrentText(preset.get("json_type", "normal"))
        self.status.setText(f"Preset '{name}' loaded")
        self.logger.log_preset_action(
            "load_completed",
            name,
            endpoint=preset["endpoint"],
            json_file=preset.get("json_file", "(none)"),
        )

    def run_multiple(self: _PresetHandlingProtocol) -> None:  # type: ignore[misc]
        """Open the multi-select dialog and run selected presets sequentially."""
        names = [self.preset_combo.itemText(i) for i in range(self.preset_combo.count())]
        if not names:
            QMessageBox.warning(self, "Error", "No presets available")
            return

        dlg = MultiSelectDialog(names)
        if not dlg.exec() or not dlg.selected:
            return

        ip = self.ip_edit.text().strip()
        if not ip:
            QMessageBox.warning(self, "Error", "Device IP required")
            return
        if not self._validate_ip(ip):
            QMessageBox.warning(self, "Error", "Invalid IP address format")
            return
        if not self.user_edit.text().strip():
            QMessageBox.warning(self, "Error", "Username required for authentication")
            return

        self.total_request_count = len(dlg.selected)
        self.current_request_count = 0
        self.status.setText(f"Running {self.total_request_count} presets...")

        try:
            log_file = self.requests.start_new_log("MultiPreset_Run")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create log file: {e}")
            return

        # Read password once; each worker gets its own bytearray copy to zero independently
        raw_password = self.pass_edit.text()
        queue: deque[str] = deque(dlg.selected)

        def run_next() -> None:
            """Send the next queued preset, or finish when the queue is empty."""
            if not queue:
                self.status.setText("All presets finished")
                return

            preset_name = queue.popleft()
            self.current_request_count += 1
            self._update_progress(self.current_request_count, self.total_request_count)

            preset = self.presets.get_by_name(preset_name)
            if not preset:
                self.status.setText(f"Skipping invalid preset: {preset_name}")
                QTimer.singleShot(0, run_next)
                return

            def on_response(text: str, pname: str, tag: str) -> None:
                self.display_response(text, pname, tag)
                self._update_progress(self.current_request_count, self.total_request_count)
                QTimer.singleShot(0, run_next)

            try:
                worker = self.requests.send_request_async(
                    ip,
                    self.user_edit.text(),
                    bytearray(raw_password.encode("utf-8")),
                    preset["endpoint"],
                    preset["json_file"],
                    self.simple_check.isChecked(),
                    preset["json_type"],
                    on_response,
                    preset_name=preset_name,
                    log_file=log_file,
                )
                self._track_request(worker)
                worker.finished.connect(lambda *_: self._untrack_request(worker))
            except Exception as e:
                self.status.setText(f"Failed to send {preset_name}: {e}")
                QTimer.singleShot(0, run_next)

        run_next()
