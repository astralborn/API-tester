"""Request handling mixin for API Test Tool."""
from __future__ import annotations

import ipaddress
import json
from typing import TYPE_CHECKING

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QWidget,
)

if TYPE_CHECKING:
    from config.di_container import RequestManagerProtocol
    from config.logging_system import StructuredLogger
    from managers.requests_manager import RequestWorker

    class _RequestHandlingProtocol(QWidget):
        """Typed view of the fully-assembled host class, for use in method stubs."""

        ip_edit: QLineEdit
        user_edit: QLineEdit
        pass_edit: QLineEdit
        simple_check: QCheckBox
        endpoint_combo: QComboBox
        json_combo: QComboBox
        json_type_combo: QComboBox
        btn_cancel: QPushButton
        status: QLabel
        response: QTextEdit
        active_requests: list[RequestWorker]
        current_request_count: int
        total_request_count: int
        requests: RequestManagerProtocol
        logger: StructuredLogger


        # Internal methods referenced across methods
        def _validate_ip(self, ip: str) -> bool: ...
        def _track_request(self, worker: RequestWorker) -> None: ...
        def _untrack_request(self, worker: RequestWorker) -> None: ...
        def display_response(self, text: str, preset_name: str, tag: str) -> None: ...
        def _format_json_response(self, text: str) -> str: ...
        def _build_response_html(self, text: str, preset_name: str, tag: str) -> str: ...
        def _escape_html(self, text: str) -> str: ...
else:
    _RequestHandlingProtocol = object


class RequestHandlingMixin(_RequestHandlingProtocol):  # type: ignore[misc]
    """Mixin that handles sending, cancelling, and displaying HTTP requests."""

    def _validate_ip(self, ip: str) -> bool:
        """Return True if *ip* is a valid IPv4 or IPv6 address."""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    def send_request(self: _RequestHandlingProtocol) -> None:  # type: ignore[misc]
        """Validate inputs and fire a single async HTTP request."""
        ip = self.ip_edit.text().strip()
        if not ip:
            self.logger.log_user_action("send_request_failed", reason="no_ip")
            QMessageBox.warning(self, "Error", "Device IP required")
            return

        if not self._validate_ip(ip):
            self.logger.log_user_action("send_request_failed", reason="invalid_ip", ip=ip)
            QMessageBox.warning(self, "Error", "Invalid IP address format")
            return

        if not self.user_edit.text().strip():
            self.logger.log_user_action("send_request_failed", reason="no_username")
            QMessageBox.warning(self, "Error", "Username required for authentication")
            return

        endpoint = self.endpoint_combo.currentText()
        self.logger.log_user_action(
            "send_request_started",
            ip=ip,
            endpoint=endpoint,
            json_file=self.json_combo.currentText(),
        )
        self.status.setText("Sending request...")

        def on_response(text: str, preset_name: str, tag: str) -> None:
            self.display_response(text, preset_name, tag)
            self.status.setText("Request finished successfully")
            self.logger.log_request(
                "POST",
                f"http://{ip}{endpoint}",
                200 if tag == "ok" else 400,
                0.0,
                preset_name=preset_name,
                response_tag=tag,
            )

        try:
            # Encode to bytearray so RequestWorker can zero it after use
            password = bytearray(self.pass_edit.text().encode("utf-8"))
            worker = self.requests.send_request_async(
                ip,
                self.user_edit.text(),
                password,
                endpoint,
                self.json_combo.currentText(),
                self.simple_check.isChecked(),
                self.json_type_combo.currentText(),
                on_response,
                preset_name=self.endpoint_combo.currentText(),
            )
            self._track_request(worker)
            worker.finished.connect(lambda *_: self._untrack_request(worker))

        except Exception as e:
            self.logger.exception("Failed to send request", ip=ip, endpoint=endpoint)
            QMessageBox.critical(self, "Error", f"Failed to send request: {e}")
            self.status.setText("Request failed")

    def cancel_all_requests(self: _RequestHandlingProtocol) -> None:  # type: ignore[misc]
        """Terminate all in-flight request workers immediately."""
        if not self.active_requests:
            return
        for worker in self.active_requests:
            worker.terminate()
            worker.wait()
        self.active_requests.clear()
        self.current_request_count = 0
        self.total_request_count = 0
        self.btn_cancel.setEnabled(False)
        self.status.setText("All requests cancelled")

    def _track_request(self: _RequestHandlingProtocol, worker: RequestWorker) -> None:  # type: ignore[misc]
        """Register *worker* as active and enable the Cancel button."""
        self.active_requests.append(worker)
        self.current_request_count += 1
        if len(self.active_requests) == 1:
            self.btn_cancel.setEnabled(True)

    def _untrack_request(self: _RequestHandlingProtocol, worker: RequestWorker) -> None:  # type: ignore[misc]
        """Remove *worker* from the active list; disable Cancel when idle."""
        if worker in self.active_requests:
            self.active_requests.remove(worker)
        if not self.active_requests:
            self.btn_cancel.setEnabled(False)
            self.current_request_count = 0
            self.total_request_count = 0

    def _update_progress(self: _RequestHandlingProtocol, completed: int, total: int) -> None:  # type: ignore[misc]
        """Update the status bar with the current batch progress."""
        if total > 1:
            self.status.setText(f"Progress: {completed}/{total} requests")

    def _format_json_response(self, text: str) -> str:
        """Pretty-print the JSON portion of *text*, leaving any prefix intact."""
        try:
            if "{" in text:
                idx = text.index("{")
                obj = json.loads(text[idx:])
                return text[:idx] + json.dumps(obj, indent=2, ensure_ascii=False)
        except Exception:
            pass
        return text

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters in *text*."""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _build_response_html(self, text: str, preset_name: str, tag: str) -> str:
        """Return an HTML snippet for one response entry.

        :param text: The plain-text response body.
        :param preset_name: Name of the preset that produced this response.
        :param tag: Response tag (``"ok"``, ``"warn"``, or ``"err"``).
        :returns: An HTML string ready for insertion into the response QTextEdit.
        """
        separator = '<div style="border-top: 1px solid #c0c0c0; margin: 4px 0;"></div>'
        header_style = (
            "font-weight: 600; color: #666666; margin-bottom: 8px; "
            "font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;"
        )
        body_style = (
            "font-family: Consolas, monospace; font-size: 12px; "
            "line-height: 1.5; color: #333333;"
        )
        header = f'<div style="{header_style}">{preset_name or "Request"}</div><br>'
        body = self._escape_html(text).replace("\n", "<br>")
        return f'{separator}<div style="{body_style}">{header}{body}</div>'

    def display_response(self: _RequestHandlingProtocol, text: str, preset_name: str, tag: str) -> None:  # type: ignore[misc]
        """Format and append *text* to the response viewer.

        :param text: Raw response text returned by the request worker.
        :param preset_name: Preset name shown as the entry header.
        :param tag: Response tag used for colouring/logging.
        """
        formatted = self._format_json_response(text)
        html = self._build_response_html(formatted, preset_name, tag)
        self.response.moveCursor(QTextCursor.MoveOperation.End)
        self.response.insertHtml(html)
        self.response.moveCursor(QTextCursor.MoveOperation.End)

    def clear_response(self: _RequestHandlingProtocol) -> None:  # type: ignore[misc]
        """Clear all content from the response viewer."""
        self.response.clear()
