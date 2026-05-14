"""Dialogs for API Test Tool — modern design."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

_CARD_BG = "#FFFFFF"
_BG = "#FAFAFA"
_BORDER = "#E2E2E8"
_TEXT = "#0F0F11"
_MUTED = "#6B7280"
_ACCENT = "#2563EB"
_ACCENT_HVR = "#1D4ED8"
_BTN_SEC = "#FFFFFF"
_BTN_SEC_HVR = "#F0F0F2"

_DIALOG_QSS = f"""
QDialog {{
    background-color: {_BG};
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    font-size: 13px;
    color: {_TEXT};
}}
QLabel {{ background: transparent; border: none; color: {_TEXT}; }}
QCheckBox {{
    color: {_MUTED}; spacing: 8px; background: transparent;
}}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1.5px solid {_BORDER}; border-radius: 4px;
    background-color: {_CARD_BG};
}}
QCheckBox::indicator:hover {{ border-color: {_ACCENT}; }}
QCheckBox::indicator:checked {{
    background-color: {_ACCENT}; border-color: {_ACCENT};
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEwIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgNEwzLjUgNi41TDkgMS41IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlbGluZWpvaW49InJvdW5kIi8+PC9zdmc+);
}}
QListWidget {{
    background-color: {_CARD_BG}; border: 1.5px solid {_BORDER};
    border-radius: 10px; padding: 6px; outline: none; color: {_TEXT};
}}
QListWidget::item {{ padding: 8px 10px; border-radius: 6px; color: {_TEXT}; }}
QListWidget::item:selected {{ background-color: #EFF6FF; color: {_ACCENT}; }}
QListWidget::item:hover:!selected {{ background-color: {_BG}; }}
QScrollBar:vertical {{ background: transparent; width: 8px; }}
QScrollBar::handle:vertical {{
    background: #D1D5DB; border-radius: 4px; min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QPushButton {{
    background-color: {_ACCENT}; color: #FFFFFF; border: none;
    border-radius: 8px; padding: 8px 20px;
    font-weight: 600; font-size: 13px; min-height: 34px;
}}
QPushButton:hover {{ background-color: {_ACCENT_HVR}; }}
QPushButton:pressed {{ background-color: #1E40AF; }}
QPushButton[secondary="true"] {{
    background-color: {_BTN_SEC}; color: {_TEXT};
    border: 1.5px solid {_BORDER};
}}
QPushButton[secondary="true"]:hover {{
    background-color: {_BTN_SEC_HVR}; border-color: #BBBBC8;
}}
"""


class MultiSelectDialog(QDialog):
    """Dialog that lets the user choose multiple presets to run sequentially."""

    def __init__(self, items: list[str]) -> None:
        """Initialise the dialog and populate it with *items*.

        :param items: List of preset names to display in the list widget.
        """
        super().__init__()
        self.setWindowTitle("Run Multiple Presets")
        self.setMinimumSize(480, 560)
        self.setStyleSheet(_DIALOG_QSS)
        self.selected: list[str] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        title = QLabel("Select Presets to Run")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {_TEXT};")
        subtitle = QLabel("Choose the presets you want to execute sequentially.")
        subtitle.setStyleSheet(f"font-size: 12px; color: {_MUTED};")
        root.addWidget(title)
        root.addWidget(subtitle)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {_BORDER}; max-height: 1px; border: none;")
        root.addWidget(sep)

        self.select_all_cb = QCheckBox("Select all")
        self.select_all_cb.stateChanged.connect(self.toggle_select_all)
        root.addWidget(self.select_all_cb)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for item in items:
            self.list_widget.addItem(QListWidgetItem(item))
        root.addWidget(self.list_widget, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("secondary", True)
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self.reject)

        ok_btn = QPushButton("Run Selected")
        ok_btn.setFixedWidth(130)
        ok_btn.clicked.connect(self.accept_selection)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        root.addLayout(btn_row)

    def toggle_select_all(self, state: int) -> None:
        """Select or deselect all items based on the *Select all* checkbox.

        :param state: Qt check state integer (``Qt.Checked`` selects all).
        """
        checked = state == Qt.CheckState.Checked
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setSelected(checked)

    def accept_selection(self) -> None:
        """Store the selected item names and close the dialog with accept."""
        self.selected = [item.text() for item in self.list_widget.selectedItems()]
        self.accept()
