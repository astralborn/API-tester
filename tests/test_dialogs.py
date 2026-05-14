"""Tests for app/dialogs.py — MultiSelectDialog.

HOW THESE TESTS RUN WITHOUT SHOWING A WINDOW
=============================================
MultiSelectDialog is a QDialog subclass, so a QApplication must exist — that is
provided by the qapp fixture from pytest-qt (same as test_app_widget.py).
The dialog is instantiated and exercised entirely in memory: no .exec() is ever
called, so the Qt event loop never spins and no window appears on screen.
Individual methods (toggle_select_all, accept_selection) are called directly.
"""
from __future__ import annotations

import pytest

from app.dialogs import MultiSelectDialog


@pytest.fixture()
def dialog(qapp):
    """A MultiSelectDialog pre-populated with three items, not shown."""
    return MultiSelectDialog(["Alpha", "Beta", "Gamma"])


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_has_correct_item_count(self, dialog):
        # list_widget should contain exactly the items passed in
        assert dialog.list_widget.count() == 3

    def test_items_match_input(self, dialog):
        texts = [dialog.list_widget.item(i).text() for i in range(dialog.list_widget.count())]
        assert texts == ["Alpha", "Beta", "Gamma"]

    def test_selected_is_empty_initially(self, dialog):
        # No items chosen yet — self.selected starts as an empty list
        assert dialog.selected == []

    def test_window_title(self, dialog):
        assert dialog.windowTitle() == "Run Multiple Presets"


# ---------------------------------------------------------------------------
# toggle_select_all
# ---------------------------------------------------------------------------

class TestToggleSelectAll:
    def test_select_all_selects_every_item(self, dialog):
        from PySide6.QtCore import Qt
        # Simulate checking the "Select all" checkbox
        dialog.toggle_select_all(Qt.Checked)
        for i in range(dialog.list_widget.count()):
            assert dialog.list_widget.item(i).isSelected()

    def test_uncheck_all_deselects_every_item(self, dialog):
        from PySide6.QtCore import Qt
        # First select all, then deselect all
        dialog.toggle_select_all(Qt.Checked)
        dialog.toggle_select_all(Qt.Unchecked)
        for i in range(dialog.list_widget.count()):
            assert not dialog.list_widget.item(i).isSelected()


# ---------------------------------------------------------------------------
# accept_selection
# ---------------------------------------------------------------------------

class TestAcceptSelection:
    def test_accept_selection_records_selected_items(self, dialog):
        # Select first and last items manually
        dialog.list_widget.item(0).setSelected(True)
        dialog.list_widget.item(2).setSelected(True)
        # Call accept_selection directly (avoids actually closing the dialog)
        dialog.accept_selection()
        assert "Alpha" in dialog.selected
        assert "Gamma" in dialog.selected
        assert "Beta" not in dialog.selected

    def test_accept_selection_with_none_selected(self, dialog):
        dialog.accept_selection()
        assert dialog.selected == []

    def test_accept_selection_all_selected(self, dialog):
        from PySide6.QtCore import Qt
        dialog.toggle_select_all(Qt.Checked)
        dialog.accept_selection()
        assert dialog.selected == ["Alpha", "Beta", "Gamma"]

    def test_empty_dialog_accept(self, qapp):
        # Edge case: dialog built with no items
        dlg = MultiSelectDialog([])
        dlg.accept_selection()
        assert dlg.selected == []

