"""Tests for app/preset_handling.py — PresetHandlingMixin (pure-logic method)."""
from __future__ import annotations

import pytest
from tests.helpers import SAMPLE_PRESETS


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def mixin():
    """Bare PresetHandlingMixin instance — no Qt, no __init__ called."""
    from app.preset_handling import PresetHandlingMixin

    class Stub(PresetHandlingMixin):
        pass

    return Stub.__new__(Stub)


# ---------------------------------------------------------------------------
# _preset_matches
# ---------------------------------------------------------------------------

class TestPresetMatches:

    # ---- happy / unhappy filtering ----

    def test_happy_mode_excludes_unhappy_json(self, mixin):
        preset = {"name": "X", "json_file": "get/unhappy/foo.json"}
        assert mixin._preset_matches(preset, "happy", "") is False

    def test_happy_mode_includes_happy_json(self, mixin):
        preset = {"name": "X", "json_file": "get/normal_action/foo.json"}
        assert mixin._preset_matches(preset, "happy", "") is True

    def test_unhappy_mode_excludes_happy_json(self, mixin):
        preset = {"name": "X", "json_file": "get/normal_action/foo.json"}
        assert mixin._preset_matches(preset, "unhappy", "") is False

    def test_unhappy_mode_includes_unhappy_json(self, mixin):
        preset = {"name": "X", "json_file": "get/unhappy/foo.json"}
        assert mixin._preset_matches(preset, "unhappy", "") is True

    # ---- missing json_file ----

    def test_missing_json_file_returns_false(self, mixin):
        preset = {"name": "No file"}
        assert mixin._preset_matches(preset, "happy", "") is False

    def test_empty_json_file_returns_false(self, mixin):
        preset = {"name": "Empty", "json_file": ""}
        assert mixin._preset_matches(preset, "happy", "") is False

    # ---- search string ----

    def test_search_matches_name_substring(self, mixin):
        preset = {"name": "GetContacts Happy", "json_file": "get/normal_action/foo.json"}
        assert mixin._preset_matches(preset, "happy", "contacts") is True

    def test_search_case_insensitive(self, mixin):
        preset = {"name": "GetSIPAccount", "json_file": "get/normal_action/foo.json"}
        assert mixin._preset_matches(preset, "happy", "SIPACCOUNT") is True

    def test_search_no_match_returns_false(self, mixin):
        preset = {"name": "GetContacts", "json_file": "get/normal_action/foo.json"}
        assert mixin._preset_matches(preset, "happy", "audio") is False

    # ---- Windows backslash path ----

    def test_backslash_path_treated_as_unhappy(self, mixin):
        preset = {"name": "W", "json_file": "get\\unhappy\\foo.json"}
        assert mixin._preset_matches(preset, "unhappy", "") is True

    # ---- all modes for SAMPLE_PRESETS ----

    @pytest.mark.parametrize("preset,mode,search,expected", [
        (SAMPLE_PRESETS[0], "happy",   "",           True),   # GetContacts Happy
        (SAMPLE_PRESETS[0], "unhappy", "",           False),  # GetContacts Happy vs unhappy mode
        (SAMPLE_PRESETS[1], "unhappy", "",           True),   # GetContacts Unhappy
        (SAMPLE_PRESETS[1], "happy",   "",           False),  # GetContacts Unhappy vs happy mode
        (SAMPLE_PRESETS[2], "happy",   "sipaccount", True),   # search match
        (SAMPLE_PRESETS[2], "happy",   "zzz",        False),  # search no match
    ])
    def test_sample_presets(self, mixin, preset, mode, search, expected):
        assert mixin._preset_matches(preset, mode, search) is expected
