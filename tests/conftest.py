"""Shared pytest fixtures for the API-tester test suite."""
from __future__ import annotations
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# QApplication singleton – required for any Qt widget tests
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def qapp_session(qapp):
    """Reuse a single QApplication across the whole test session."""
    return qapp


# ---------------------------------------------------------------------------
# Temporary directory helpers
# ---------------------------------------------------------------------------
@pytest.fixture()
def tmp_presets_file(tmp_path: Path) -> Path:
    """Return a temporary presets JSON file path (empty list)."""
    p = tmp_path / "presets.json"
    p.write_text("[]", encoding="utf-8")
    return p


@pytest.fixture()
def tmp_settings_file(tmp_path: Path) -> Path:
    """Return a temporary settings JSON file path."""
    p = tmp_path / "settings.json"
    p.write_text("{}", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Manager stubs / mocks
# ---------------------------------------------------------------------------
@pytest.fixture()
def mock_preset_manager() -> MagicMock:
    mgr = MagicMock()
    mgr.presets = []
    mgr.get_by_name.return_value = None
    mgr.get_names.return_value = []
    return mgr


@pytest.fixture()
def mock_request_manager() -> MagicMock:
    mgr = MagicMock()
    worker = MagicMock()
    worker.finished = MagicMock()
    worker.finished.connect = MagicMock()
    mgr.send_request_async.return_value = worker
    return mgr


@pytest.fixture()
def mock_settings_manager() -> MagicMock:
    mgr = MagicMock()
    mgr.get_last_ip.return_value = ""
    mgr.get_last_user.return_value = ""
    mgr.get_last_simple_format.return_value = False
    mgr.get_last_test_mode.return_value = "happy"
    mgr.get_last_json_type.return_value = "normal"
    mgr.get_last_endpoint.return_value = ""
    mgr.get_window_geometry.return_value = ""
    return mgr


@pytest.fixture()
def mock_logger() -> MagicMock:
    return MagicMock()


# ---------------------------------------------------------------------------
# Sample preset data (re-exported from helpers for backwards compatibility)
# ---------------------------------------------------------------------------
from tests.helpers import SAMPLE_PRESETS  # noqa: E402

