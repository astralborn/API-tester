"""UI builder module for API Test Tool — modern two-panel design."""
from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config.constants import API_ENDPOINTS

BG = "#FAFAFA"
SIDEBAR_BG = "#F0F0F2"
CARD_BG = "#FFFFFF"
BORDER = "#E2E2E8"
BORDER_FOCUS = "#2563EB"
TEXT_PRIMARY = "#0F0F11"
TEXT_MUTED = "#6B7280"
ACCENT = "#2563EB"
ACCENT_HOVER = "#1D4ED8"
BTN_BG = "#FFFFFF"
BTN_HVR = "#F0F0F2"
INPUT_BG = "#FFFFFF"
DANGER = "#DC2626"

_GLOBAL_QSS = f"""
QWidget {{
    background-color: {BG}; color: {TEXT_PRIMARY};
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 12px; border: none; outline: none;
}}
QLineEdit, QComboBox {{
    background-color: {INPUT_BG}; border: 1.5px solid {BORDER};
    border-radius: 6px; padding: 4px 10px; min-height: 26px; color: {TEXT_PRIMARY};
}}
QLineEdit:hover, QComboBox:hover {{ border-color: #BBBBC8; }}
QLineEdit:focus, QComboBox:focus {{ border-color: {BORDER_FOCUS}; background-color: {CARD_BG}; }}
QLineEdit::placeholder {{ color: {TEXT_MUTED}; }}
QComboBox::drop-down {{ width: 28px; border: none; background: transparent; }}
QComboBox::down-arrow {{
    image: none; width: 0; height: 0;
    border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 5px solid {TEXT_MUTED}; margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {CARD_BG}; border: 1.5px solid {BORDER};
    border-radius: 8px; padding: 4px;
    selection-background-color: #EFF6FF; selection-color: {ACCENT}; outline: none;
}}
QComboBox QAbstractItemView::item {{ min-height: 28px; padding: 0 8px; border-radius: 4px; }}
QPushButton {{
    background-color: {BTN_BG}; color: {TEXT_PRIMARY};
    border: 1.5px solid {BORDER}; border-radius: 6px;
    padding: 5px 16px; font-weight: 600; font-size: 12px; min-height: 28px;
}}
QPushButton:hover {{ background-color: {BTN_HVR}; border-color: #BBBBC8; }}
QPushButton:pressed {{ background-color: #E5E7EB; }}
QPushButton:disabled {{ color: #B0B0B8; border-color: {BORDER}; }}
QPushButton[danger="true"] {{
    background-color: transparent; color: {DANGER}; border: 1.5px solid #FECACA;
}}
QPushButton[danger="true"]:hover {{ background-color: #FEF2F2; border-color: {DANGER}; }}
QPushButton[danger="true"]:disabled {{
    color: #B0B0B8; border-color: {BORDER}; background-color: transparent;
}}
QCheckBox {{ color: {TEXT_MUTED}; spacing: 8px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px; border: 1.5px solid {BORDER};
    border-radius: 4px; background-color: {INPUT_BG};
}}
QCheckBox::indicator:hover {{ border-color: {BORDER_FOCUS}; }}
QCheckBox::indicator:checked {{
    background-color: {ACCENT}; border-color: {ACCENT};
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEwIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgNEwzLjUgNi41TDkgMS41IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlbGluZWpvaW49InJvdW5kIi8+PC9zdmc+);
}}
QTextEdit {{
    background-color: {CARD_BG}; border: none; padding: 16px;
    font-family: Consolas, Monaco, monospace; font-size: 12px; color: {TEXT_PRIMARY};
}}
QScrollBar:vertical {{ background: transparent; width: 8px; }}
QScrollBar::handle:vertical {{ background: #D1D5DB; border-radius: 4px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: #9CA3AF; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 8px; }}
QScrollBar::handle:horizontal {{ background: #D1D5DB; border-radius: 4px; min-width: 24px; }}
QScrollBar::handle:horizontal:hover {{ background: #9CA3AF; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QSplitter::handle {{ background-color: {BORDER}; width: 1px; }}
"""

# itertools.count() replaces the [0] mutable list hack
_card_counter = itertools.count(1)


def _card(layout_cls=QVBoxLayout, spacing: int = 7, margins=(12, 10, 12, 10)):
    """Return a bordered card widget with a unique object name.

    :param layout_cls: Layout class to apply to the card (default: QVBoxLayout).
    :param spacing: Pixel spacing between child widgets.
    :param margins: Content margins as (left, top, right, bottom).
    :returns: A ``(QWidget, layout)`` tuple ready to receive child widgets.
    """
    name = f"card_{next(_card_counter)}"
    frame = QWidget()
    frame.setObjectName(name)
    frame.setStyleSheet(f"""
        QWidget#{name} {{
            background-color: {SIDEBAR_BG};
            border: 1.5px solid {BORDER}; border-radius: 10px;
        }}
        QWidget#{name} QLabel {{ border: none; background: transparent; }}
        QWidget#{name} QCheckBox {{ border: none; background: transparent; }}
    """)
    lay = layout_cls(frame)
    lay.setSpacing(spacing)
    lay.setContentsMargins(*margins)
    return frame, lay


def _section_label(text: str) -> QLabel:
    """Return a small uppercase section-header label."""
    lbl = QLabel(text.upper())
    lbl.setStyleSheet(
        "color: #9CA3AF; font-size: 9px; font-weight: 700; "
        "letter-spacing: 1px; border: none; background: transparent; padding: 0;"
    )
    return lbl


def _field_label(text: str) -> QLabel:
    """Return a bold field-name label."""
    lbl = QLabel(text)
    lbl.setStyleSheet("font-weight: 600; border: none; background: transparent; padding: 0;")
    return lbl


if TYPE_CHECKING:
    class _UIBuilderProtocol(QWidget):
        """Typed view of the fully-assembled host class, for use in method stubs."""

        # Widgets assigned inside build_ui
        ip_edit: QLineEdit
        user_edit: QLineEdit
        pass_edit: QLineEdit
        simple_check: QCheckBox
        test_mode_combo: QComboBox
        preset_search: QLineEdit
        preset_combo: QComboBox
        endpoint_combo: QComboBox
        json_type_combo: QComboBox
        json_combo: QComboBox
        btn_send: QPushButton
        btn_multi: QPushButton
        btn_cancel: QPushButton
        btn_clear: QPushButton
        response: QTextEdit
        status_label: QLabel
        status: QLabel


        # Cross-mixin callbacks
        def _auto_save_connection_settings(self) -> None: ...
        def _auto_save_ui_settings(self) -> None: ...
        def update_presets_list(self) -> None: ...
        def on_preset_changed(self, name: str) -> None: ...
        def load_preset(self) -> None: ...
        def save_preset(self) -> None: ...
        def send_request(self) -> None: ...
        def run_multiple(self) -> None: ...
        def cancel_all_requests(self) -> None: ...
        def clear_response(self) -> None: ...
else:
    _UIBuilderProtocol = object


class UIBuilderMixin:
    """Mixin that applies the application theme and constructs the two-panel UI."""

    def apply_light_theme(self: _UIBuilderProtocol) -> None:  # type: ignore[misc]
        """Set the Qt palette and global stylesheet to the light theme."""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window,          QColor(SIDEBAR_BG))
        palette.setColor(QPalette.ColorRole.Base,            QColor(CARD_BG))
        palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(BG))
        palette.setColor(QPalette.ColorRole.Text,            QColor(TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.WindowText,      QColor(TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Button,          QColor(BTN_BG))
        palette.setColor(QPalette.ColorRole.ButtonText,      QColor(TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Highlight,       QColor(ACCENT))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        QApplication.setPalette(palette)
        self.setStyleSheet(_GLOBAL_QSS)

    def build_ui(self: _UIBuilderProtocol) -> None:  # type: ignore[misc]
        """Construct and lay out all widgets in the main window."""
        root = QHBoxLayout()
        self.setLayout(root)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter)

        # ── SIDEBAR ───────────────────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setMinimumWidth(300)
        sidebar.setMaximumWidth(400)
        sidebar.setStyleSheet(f"background-color: {SIDEBAR_BG};")
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(14, 14, 14, 12)
        sl.setSpacing(8)

        logo_row = QHBoxLayout()
        logo_row.setContentsMargins(0, 0, 0, 0)
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {ACCENT}; font-size: 13px; background: transparent; border: none;")
        title = QLabel("API Tester")
        title.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 700; "
            "background: transparent; border: none; padding: 0 0 0 5px;"
        )
        logo_row.addWidget(dot)
        logo_row.addWidget(title)
        logo_row.addStretch()
        sl.addLayout(logo_row)

        # CONNECTION
        conn_card, conn_lay = _card(QVBoxLayout, spacing=6)
        conn_lay.addWidget(_section_label("Connection"))
        conn_lay.addWidget(_field_label("Device IP"))
        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("192.168.1.100")
        self.ip_edit.textChanged.connect(self._auto_save_connection_settings)
        conn_lay.addWidget(self.ip_edit)

        creds_row = QHBoxLayout()
        creds_row.setSpacing(6)
        user_col = QVBoxLayout()
        user_col.setSpacing(3)
        user_col.addWidget(_field_label("Username"))
        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("username")
        self.user_edit.textChanged.connect(self._auto_save_connection_settings)
        user_col.addWidget(self.user_edit)
        pass_col = QVBoxLayout()
        pass_col.setSpacing(3)
        pass_col.addWidget(_field_label("Password"))
        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("••••••")
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        pass_col.addWidget(self.pass_edit)
        creds_row.addLayout(user_col)
        creds_row.addLayout(pass_col)
        conn_lay.addLayout(creds_row)

        self.simple_check = QCheckBox("Simple response format")
        self.simple_check.toggled.connect(self._auto_save_connection_settings)
        conn_lay.addWidget(self.simple_check)
        sl.addWidget(conn_card)

        # PRESET
        preset_card, preset_lay = _card(QVBoxLayout, spacing=6)
        preset_lay.addWidget(_section_label("Preset"))
        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)
        self.test_mode_combo = QComboBox()
        self.test_mode_combo.addItems(["happy", "unhappy"])
        self.test_mode_combo.setMinimumWidth(90)
        self.test_mode_combo.setMaximumWidth(110)
        self.test_mode_combo.currentTextChanged.connect(self.update_presets_list)
        self.test_mode_combo.currentTextChanged.connect(self._auto_save_ui_settings)
        self.preset_search = QLineEdit()
        self.preset_search.setPlaceholderText("Search presets…")
        self.preset_search.textChanged.connect(self.update_presets_list)
        filter_row.addWidget(self.test_mode_combo)
        filter_row.addWidget(self.preset_search, 1)
        preset_lay.addLayout(filter_row)

        preset_lay.addWidget(_field_label("Preset"))
        self.preset_combo = QComboBox()
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        preset_lay.addWidget(self.preset_combo)

        ps_btn_row = QHBoxLayout()
        ps_btn_row.setSpacing(6)
        btn_load = QPushButton("Load")
        btn_load.clicked.connect(self.load_preset)
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.save_preset)
        ps_btn_row.addWidget(btn_load)
        ps_btn_row.addWidget(btn_save)
        ps_btn_row.addStretch()
        preset_lay.addLayout(ps_btn_row)
        sl.addWidget(preset_card)

        # REQUEST
        req_card, req_lay = _card(QVBoxLayout, spacing=6)
        req_lay.addWidget(_section_label("Request"))
        req_lay.addWidget(_field_label("Endpoint"))
        endpoint_row = QHBoxLayout()
        endpoint_row.setSpacing(6)
        self.endpoint_combo = QComboBox()
        self.endpoint_combo.addItems(API_ENDPOINTS)
        self.endpoint_combo.currentTextChanged.connect(self._auto_save_ui_settings)
        self.json_type_combo = QComboBox()
        self.json_type_combo.addItems(["normal", "google", "rpc"])
        self.json_type_combo.setFixedWidth(90)
        self.json_type_combo.currentTextChanged.connect(self._auto_save_ui_settings)
        endpoint_row.addWidget(self.endpoint_combo, 1)
        endpoint_row.addWidget(self.json_type_combo)
        req_lay.addLayout(endpoint_row)

        req_lay.addWidget(_field_label("JSON File"))
        self.json_combo = QComboBox()
        self.json_combo.addItem("(none)")
        self.json_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        # Right-align text so the filename end is visible instead of the folder prefix
        self.json_combo.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        # Show full path as tooltip on hover
        self.json_combo.currentTextChanged.connect(
            lambda t: self.json_combo.setToolTip(t)
        )
        req_lay.addWidget(self.json_combo)
        sl.addWidget(req_card)

        # ACTIONS
        self.btn_send = QPushButton("Send Request")
        self.btn_send.setFixedHeight(34)
        self.btn_send.clicked.connect(self.send_request)
        sl.addWidget(self.btn_send)

        sec_actions = QHBoxLayout()
        sec_actions.setSpacing(6)
        self.btn_multi = QPushButton("Run Multiple")
        self.btn_multi.clicked.connect(self.run_multiple)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setProperty("danger", True)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_all_requests)
        sec_actions.addWidget(self.btn_multi, 1)
        sec_actions.addWidget(self.btn_cancel, 1)
        sl.addLayout(sec_actions)

        sl.addStretch()

        # STATUS BAR
        status_frame = QWidget()
        status_frame.setObjectName("statusFrame")
        status_frame.setStyleSheet(f"""
            QWidget#statusFrame {{
                background-color: {SIDEBAR_BG};
                border: 1.5px solid {BORDER}; border-radius: 8px;
            }}
            QWidget#statusFrame QLabel {{ border: none; background: transparent; }}
        """)
        status_inner = QHBoxLayout(status_frame)
        status_inner.setContentsMargins(10, 6, 10, 6)
        status_dot = QLabel("◉")
        status_dot.setStyleSheet(f"color: {ACCENT}; font-size: 10px;")
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        status_inner.addWidget(status_dot)
        status_inner.addWidget(self.status_label, 1)
        sl.addWidget(status_frame)

        splitter.addWidget(sidebar)

        # ── RESPONSE PANEL ────────────────────────────────────────────────────
        right = QWidget()
        right.setStyleSheet(f"background-color: {CARD_BG};")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        toolbar = QWidget()
        toolbar.setObjectName("toolbar")
        toolbar.setFixedHeight(44)
        toolbar.setStyleSheet(f"""
            QWidget#toolbar {{
                background-color: {CARD_BG};
                border-bottom: 1.5px solid {BORDER};
            }}
            QWidget#toolbar QLabel {{ border: none; background: transparent; }}
        """)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(20, 0, 16, 0)
        resp_title = QLabel("Response")
        resp_title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 600;")
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setFixedSize(64, 28)
        self.btn_clear.clicked.connect(self.clear_response)
        tb_layout.addWidget(resp_title)
        tb_layout.addStretch()
        tb_layout.addWidget(self.btn_clear)
        right_layout.addWidget(toolbar)

        self.response = QTextEdit(readOnly=True)
        self.response.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.response.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        right_layout.addWidget(self.response, 1)

        splitter.addWidget(right)
        splitter.setSizes([340, 860])

        self.status = self.status_label
