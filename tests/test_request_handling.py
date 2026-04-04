"""Tests for app/request_handling.py — RequestHandlingMixin (pure-logic methods).

HOW THESE TESTS RUN WITHOUT THE APP
=====================================
RequestHandlingMixin is a plain Python class — it does NOT inherit from QWidget.
It only holds logic methods (_validate_ip, _format_json_response, etc.).
This means we can instantiate it in a normal Python process with no Qt event loop,
no QApplication, and no visible window. pytest just runs it like any other module.

The three techniques used throughout this file to make that possible are:
  1. __new__  — skips __init__ so no Qt setup code ever runs.
  2. MagicMock — replaces Qt widget attributes (status label, logger, response box)
                 with fake objects that silently absorb any call made to them.
  3. Parametrize — lets one test function cover many inputs without duplicating code.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers — build a lightweight mixin instance without a real QWidget
# ---------------------------------------------------------------------------

def _make_mixin():
    """Instantiate RequestHandlingMixin in isolation (no Qt needed).

    Technique 1 — subclass without adding anything:
        'class Stub(RequestHandlingMixin): pass'
        Stub inherits every logic method from the mixin but has no __init__
        of its own, so we control exactly how the object is created.

    Technique 2 — __new__ instead of __init__:
        'Stub.__new__(Stub)' allocates the object in memory but never calls
        __init__. This is crucial because a real QWidget.__init__ would need
        a running QApplication and would try to create OS-level window handles.
        By bypassing it we get a blank Python object that just carries the
        mixin methods — nothing Qt-related runs.

    Technique 3 — MagicMock as stand-ins for Qt widgets:
        The mixin methods occasionally call self.status.setText(...) or
        self.logger.log_user_action(...). In the real app those are Qt widgets
        and a structlog logger. Here we replace them with MagicMock objects.
        MagicMock accepts ANY attribute access and ANY method call without
        raising, and records every call so tests can assert on them later
        (see TestUpdateProgress below).
    """
    from app.request_handling import RequestHandlingMixin

    class Stub(RequestHandlingMixin):
        pass

    # Allocate the object without running __init__ (no Qt, no window, no event loop)
    obj = Stub.__new__(Stub)

    # Attach fakes for the Qt/logger attributes the mixin methods may touch.
    # Any call like obj.logger.log_user_action("x") silently succeeds and is recorded.
    obj.logger = MagicMock()   # replaces the structlog logger
    obj.status = MagicMock()   # replaces the QLabel status bar
    obj.response = MagicMock() # replaces the QTextEdit response widget
    return obj


# ---------------------------------------------------------------------------
# _validate_ip
# ---------------------------------------------------------------------------
# _validate_ip uses only Python's stdlib ipaddress module — zero Qt dependency.
# pytest.mark.parametrize runs the same test function once per value in the list,
# so 6 valid IPs → 6 separate test cases, 6 invalid IPs → 6 more, all from 2 methods.

class TestValidateIp:
    def setup_method(self):
        # setup_method runs before every test method in this class,
        # giving each test a fresh mixin instance with clean MagicMocks.
        self.mixin = _make_mixin()

    @pytest.mark.parametrize("ip", [
        "192.168.1.1",
        "10.0.0.1",
        "255.255.255.255",
        "0.0.0.0",
        "::1",          # IPv6 loopback
        "2001:db8::1",  # IPv6 documentation address
    ])
    def test_valid_ips(self, ip):
        assert self.mixin._validate_ip(ip) is True

    @pytest.mark.parametrize("ip", [
        "",                 # empty string
        "999.999.999.999",  # out-of-range octets
        "hello",            # not an IP at all
        "192.168.1",        # only 3 octets
        "192.168.1.1.1",    # 5 octets
        "abc::xyz",         # invalid IPv6 hex
    ])
    def test_invalid_ips(self, ip):
        assert self.mixin._validate_ip(ip) is False


# ---------------------------------------------------------------------------
# _format_json_response
# ---------------------------------------------------------------------------
# _format_json_response uses only Python's json module — no Qt.
# It finds the first '{' or '[' in the text, tries to parse from there,
# and returns pretty-printed JSON if successful, or the original text if not.

class TestFormatJsonResponse:
    def setup_method(self):
        self.mixin = _make_mixin()

    def test_pretty_prints_valid_json(self):
        # A realistic server response: status line followed by JSON body.
        # The method should locate '{', parse the JSON, and reformat it.
        text = 'Status: 200\n{"a":1,"b":2}'
        result = self.mixin._format_json_response(text)
        assert '"a": 1' in result
        assert '"b": 2' in result

    def test_returns_original_on_plain_text(self):
        # No '{' or '[' → nothing to parse → original returned unchanged.
        text = "No JSON here at all"
        assert self.mixin._format_json_response(text) == text

    def test_returns_original_on_invalid_json(self):
        # '{' found but the content isn't valid JSON → original returned unchanged.
        text = "prefix{bad json}"
        result = self.mixin._format_json_response(text)
        assert result == text

    def test_preserves_prefix_before_brace(self):
        # Everything before the first '{' must be kept intact in the output.
        text = "URL: http://x\n{}"
        result = self.mixin._format_json_response(text)
        assert result.startswith("URL: http://x\n")

    def test_empty_string(self):
        # Edge case: empty input → empty output, no crash.
        assert self.mixin._format_json_response("") == ""


# ---------------------------------------------------------------------------
# _escape_html
# ---------------------------------------------------------------------------
# _escape_html is pure string manipulation — replaces &, <, > with HTML entities.
# Completely independent of Qt; no mixin state used at all.

class TestEscapeHtml:
    def setup_method(self):
        self.mixin = _make_mixin()

    def test_escapes_ampersand(self):
        assert "&amp;" in self.mixin._escape_html("a & b")

    def test_escapes_less_than(self):
        assert "&lt;" in self.mixin._escape_html("<tag>")

    def test_escapes_greater_than(self):
        assert "&gt;" in self.mixin._escape_html("<tag>")

    def test_no_change_for_plain_text(self):
        # Nothing to escape → string passes through unchanged.
        assert self.mixin._escape_html("hello") == "hello"

    def test_all_three_chars(self):
        # All three special characters present in one string.
        result = self.mixin._escape_html("a < b & c > d")
        assert "&lt;" in result
        assert "&amp;" in result
        assert "&gt;" in result


# ---------------------------------------------------------------------------
# _build_response_html
# ---------------------------------------------------------------------------
# _build_response_html assembles an HTML string from parts — no Qt rendering.
# It calls _escape_html internally and produces a string; the real app then
# hands that string to a QTextEdit, but that step is NOT tested here.

class TestBuildResponseHtml:
    def setup_method(self):
        self.mixin = _make_mixin()

    def test_contains_preset_name(self):
        html = self.mixin._build_response_html("body", "MyPreset", "ok")
        assert "MyPreset" in html

    def test_contains_body_text(self):
        html = self.mixin._build_response_html("hello world", "P", "ok")
        assert "hello world" in html

    def test_newlines_converted_to_br(self):
        # Multi-line response bodies must use <br> tags so HTML renders correctly.
        html = self.mixin._build_response_html("line1\nline2", "P", "ok")
        assert "<br>" in html

    def test_html_special_chars_escaped(self):
        # Body text goes through _escape_html before being embedded in HTML.
        html = self.mixin._build_response_html("<b>bold</b>", "P", "ok")
        assert "&lt;b&gt;" in html

    def test_fallback_label_when_no_preset_name(self):
        # When no preset name is provided the method should show a generic label.
        html = self.mixin._build_response_html("body", "", "ok")
        assert "Request" in html


# ---------------------------------------------------------------------------
# _update_progress
# ---------------------------------------------------------------------------
# _update_progress calls self.status.setText(...) when there are multiple requests.
# self.status is a MagicMock, so:
#   - The call doesn't crash (no real Qt widget needed).
#   - We can assert on WHAT was passed to setText using MagicMock's call-tracking API:
#       .assert_called_once()          → was setText called exactly once?
#       .call_args[0][0]               → what string was the first positional argument?

class TestUpdateProgress:
    def test_sets_status_when_total_gt_one(self):
        mixin = _make_mixin()
        mixin._update_progress(3, 10)
        # MagicMock recorded the call; verify setText was invoked with "3" and "10" in the text.
        mixin.status.setText.assert_called_once()
        call_arg = mixin.status.setText.call_args[0][0]
        assert "3" in call_arg and "10" in call_arg

    def test_does_not_set_status_when_total_is_one(self):
        mixin = _make_mixin()
        mixin._update_progress(1, 1)
        # Single request — no progress counter shown, so setText must NOT have been called.
        mixin.status.setText.assert_not_called()


# ---------------------------------------------------------------------------
# _track_request / _untrack_request
# ---------------------------------------------------------------------------
# These manage self.active_requests and self.btn_cancel.
# Both are pure list/flag logic — no Qt event loop needed.

class TestTrackUntrack:
    def setup_method(self):
        self.mixin = _make_mixin()
        self.mixin.active_requests = []
        self.mixin.current_request_count = 0
        self.mixin.total_request_count = 0
        self.mixin.btn_cancel = MagicMock()

    def test_track_appends_worker(self):
        w = MagicMock()
        self.mixin._track_request(w)
        assert w in self.mixin.active_requests

    def test_track_enables_cancel_button_on_first_worker(self):
        self.mixin._track_request(MagicMock())
        self.mixin.btn_cancel.setEnabled.assert_called_with(True)

    def test_untrack_removes_worker(self):
        w = MagicMock()
        self.mixin.active_requests = [w]
        self.mixin._untrack_request(w)
        assert w not in self.mixin.active_requests

    def test_untrack_disables_cancel_when_list_empty(self):
        w = MagicMock()
        self.mixin.active_requests = [w]
        self.mixin._untrack_request(w)
        self.mixin.btn_cancel.setEnabled.assert_called_with(False)

    def test_untrack_leaves_cancel_enabled_when_others_remain(self):
        w1, w2 = MagicMock(), MagicMock()
        self.mixin.active_requests = [w1, w2]
        self.mixin._untrack_request(w1)
        # btn_cancel.setEnabled(False) must NOT have been called — w2 still active
        calls = [c for c in self.mixin.btn_cancel.setEnabled.call_args_list
                 if c == ((False,), {})]
        assert len(calls) == 0

    def test_untrack_unknown_worker_is_noop(self):
        self.mixin.active_requests = []
        self.mixin._untrack_request(MagicMock())  # must not raise


# ---------------------------------------------------------------------------
# display_response
# ---------------------------------------------------------------------------
# display_response calls _format_json_response → _build_response_html → insertHtml.
# self.response is a MagicMock, so insertHtml is recorded without needing a real widget.

class TestDisplayResponse:
    def test_calls_insert_html(self):
        mixin = _make_mixin()
        mixin.display_response("hello", "MyPreset", "ok")
        mixin.response.insertHtml.assert_called_once()

    def test_inserted_html_contains_body_text(self):
        mixin = _make_mixin()
        mixin.display_response("response body", "P", "ok")
        html_arg = mixin.response.insertHtml.call_args[0][0]
        assert "response body" in html_arg

    def test_moves_cursor_to_end(self):
        mixin = _make_mixin()
        mixin.display_response("x", "P", "ok")
        # moveCursor must be called at least once (before and after insertHtml)
        assert mixin.response.moveCursor.call_count >= 1


