"""Tests for managers/presets.py — PresetManager."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_manager(presets_file: Path):
    """Return a PresetManager wired to *presets_file*."""
    from managers.presets import PresetManager
    return PresetManager(presets_file=presets_file)


# ---------------------------------------------------------------------------
# load_presets
# ---------------------------------------------------------------------------

class TestLoadPresets:
    def test_loads_empty_list_when_file_missing(self, tmp_path):
        missing = tmp_path / "no_such.json"
        mgr = _make_manager(missing)
        assert mgr.presets == []

    def test_loads_presets_from_existing_file(self, tmp_path):
        data = [{"name": "A", "endpoint": "/x", "json_file": "a.json",
                 "simple_format": False, "json_type": "normal"}]
        f = tmp_path / "presets.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        mgr = _make_manager(f)
        assert len(mgr.presets) == 1
        assert mgr.presets[0]["name"] == "A"

    def test_uses_empty_list_on_corrupt_file(self, tmp_path):
        f = tmp_path / "presets.json"
        f.write_text("NOT_JSON", encoding="utf-8")
        mgr = _make_manager(f)
        assert mgr.presets == []


# ---------------------------------------------------------------------------
# add_preset / get_by_name
# ---------------------------------------------------------------------------

class TestAddAndGet:
    def test_add_new_preset(self, tmp_path):
        mgr = _make_manager(tmp_path / "p.json")
        preset = {"name": "Test", "endpoint": "/x", "json_file": "t.json",
                  "simple_format": False, "json_type": "normal"}
        mgr.add_preset(preset)
        assert mgr.get_by_name("Test") == preset

    def test_add_replaces_existing(self, tmp_path):
        f = tmp_path / "p.json"
        f.write_text(
            json.dumps([{"name": "X", "endpoint": "/old", "json_file": "o.json",
                         "simple_format": False, "json_type": "normal"}]),
            encoding="utf-8"
        )
        mgr = _make_manager(f)
        mgr.add_preset({"name": "X", "endpoint": "/new", "json_file": "n.json",
                        "simple_format": True, "json_type": "google"})
        assert len(mgr.presets) == 1
        assert mgr.presets[0]["endpoint"] == "/new"

    def test_add_without_name_is_no_op(self, tmp_path):
        mgr = _make_manager(tmp_path / "p.json")
        mgr.add_preset({"endpoint": "/x"})
        assert mgr.presets == []

    def test_get_by_name_returns_none_for_missing(self, tmp_path):
        mgr = _make_manager(tmp_path / "p.json")
        assert mgr.get_by_name("ghost") is None


# ---------------------------------------------------------------------------
# save_presets / persistence round-trip
# ---------------------------------------------------------------------------

class TestSavePresets:
    def test_persists_to_disk(self, tmp_path):
        f = tmp_path / "p.json"
        mgr = _make_manager(f)
        mgr.add_preset({"name": "Save Me", "endpoint": "/s", "json_file": "s.json",
                        "simple_format": False, "json_type": "normal"})
        # Re-load from same file
        mgr2 = _make_manager(f)
        assert mgr2.get_by_name("Save Me") is not None

    def test_save_fails_silently_on_bad_path(self, tmp_path):
        """Should not raise even when the file cannot be written."""
        mgr = _make_manager(tmp_path / "p.json")
        mgr.presets = [{"name": "X"}]
        # Replace the internal _file with a directory — open() on a dir raises OSError
        bad = tmp_path / "subdir"
        bad.mkdir()
        mgr._file = bad
        mgr.save_presets()  # must not raise


# ---------------------------------------------------------------------------
# delete_preset
# ---------------------------------------------------------------------------

class TestDeletePreset:
    def test_delete_existing(self, tmp_path):
        f = tmp_path / "p.json"
        f.write_text(
            json.dumps([{"name": "Del", "endpoint": "/d", "json_file": "d.json",
                         "simple_format": False, "json_type": "normal"}]),
            encoding="utf-8"
        )
        mgr = _make_manager(f)
        result = mgr.delete_preset("Del")
        assert result is True
        assert mgr.get_by_name("Del") is None

    def test_delete_nonexistent_returns_false(self, tmp_path):
        mgr = _make_manager(tmp_path / "p.json")
        assert mgr.delete_preset("ghost") is False

    def test_delete_persists(self, tmp_path):
        f = tmp_path / "p.json"
        f.write_text(
            json.dumps([{"name": "Gone", "endpoint": "/g", "json_file": "g.json",
                         "simple_format": False, "json_type": "normal"}]),
            encoding="utf-8"
        )
        mgr = _make_manager(f)
        mgr.delete_preset("Gone")
        mgr2 = _make_manager(f)
        assert mgr2.get_by_name("Gone") is None


# ---------------------------------------------------------------------------
# get_names
# ---------------------------------------------------------------------------

class TestGetNames:
    def test_returns_list_of_names(self, tmp_path):
        f = tmp_path / "p.json"
        data = [
            {"name": "A", "endpoint": "/a", "json_file": "a.json",
             "simple_format": False, "json_type": "normal"},
            {"name": "B", "endpoint": "/b", "json_file": "b.json",
             "simple_format": False, "json_type": "normal"},
        ]
        f.write_text(json.dumps(data), encoding="utf-8")
        mgr = _make_manager(f)
        assert mgr.get_names() == ["A", "B"]

    def test_empty_when_no_presets(self, tmp_path):
        mgr = _make_manager(tmp_path / "p.json")
        assert mgr.get_names() == []

