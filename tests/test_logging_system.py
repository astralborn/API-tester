"""Tests for config/logging_system.py — StructuredLogger, formatters, LoggingManager.

HOW THESE TESTS RUN WITHOUT THE APP
=====================================
The logging system is pure Python — no Qt involved at all. Every class here
writes to ordinary file handlers and the stdlib logging module.
Tests create loggers pointed at tmp_path (a pytest-provided temporary directory)
so they never touch the real logs/ folder and leave no side effects.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from config.logging_system import (
    ColoredFormatter,
    JsonFormatter,
    LoggingManager,
    StructuredLogger,
    cleanup_logging,
    get_logger,
    set_logging_level,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_logger(tmp_path: Path, name: str = "test_logger") -> StructuredLogger:
    """Return a StructuredLogger that writes into tmp_path, not logs/."""
    logger = StructuredLogger.__new__(StructuredLogger)
    logger.name = name
    logger.log_dir = tmp_path

    # Build a real stdlib logger wired to our tmp directory
    logger.logger = logging.getLogger(f"_test_{name}")
    logger.logger.setLevel(logging.DEBUG)
    logger.logger.handlers.clear()
    logger.logger.propagate = False

    # Plain file handler — enough to verify writes without rotating-file complexity
    handler = logging.FileHandler(tmp_path / f"{name}.log", encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.logger.addHandler(handler)

    return logger


# ---------------------------------------------------------------------------
# StructuredLogger — basic log-level methods
# ---------------------------------------------------------------------------

class TestStructuredLoggerLevels:
    """Each method on StructuredLogger delegates to the stdlib logger at the right level."""

    def test_debug_writes_at_debug(self, tmp_path):
        lg = _make_logger(tmp_path)
        lg.debug("dbg msg")
        content = (tmp_path / "test_logger.log").read_text()
        assert "dbg msg" in content

    def test_info_writes_at_info(self, tmp_path):
        lg = _make_logger(tmp_path)
        lg.info("info msg")
        content = (tmp_path / "test_logger.log").read_text()
        assert "info msg" in content

    def test_warning_writes_at_warning(self, tmp_path):
        lg = _make_logger(tmp_path)
        lg.warning("warn msg")
        content = (tmp_path / "test_logger.log").read_text()
        assert "warn msg" in content

    def test_error_writes_at_error(self, tmp_path):
        lg = _make_logger(tmp_path)
        lg.error("err msg")
        content = (tmp_path / "test_logger.log").read_text()
        assert "err msg" in content

    def test_critical_writes_at_critical(self, tmp_path):
        lg = _make_logger(tmp_path)
        lg.critical("crit msg")
        content = (tmp_path / "test_logger.log").read_text()
        assert "crit msg" in content

    def test_exception_writes_at_error(self, tmp_path):
        # exception() logs at ERROR level and captures exc_info
        lg = _make_logger(tmp_path)
        try:
            raise ValueError("boom")
        except ValueError:
            lg.exception("caught it")
        content = (tmp_path / "test_logger.log").read_text()
        assert "caught it" in content


# ---------------------------------------------------------------------------
# StructuredLogger — convenience methods
# ---------------------------------------------------------------------------

class TestStructuredLoggerConvenience:
    def test_log_request_includes_method_url_and_status(self, tmp_path):
        lg = _make_logger(tmp_path)
        lg.log_request("POST", "http://10.0.0.1/api", 200, 0.123)
        content = (tmp_path / "test_logger.log").read_text()
        assert "POST" in content
        assert "http://10.0.0.1/api" in content
        assert "200" in content

    def test_log_preset_action_includes_action_and_name(self, tmp_path):
        lg = _make_logger(tmp_path)
        lg.log_preset_action("save_started", "MyPreset")
        content = (tmp_path / "test_logger.log").read_text()
        assert "save_started" in content
        assert "MyPreset" in content

    def test_log_user_action_includes_action(self, tmp_path):
        lg = _make_logger(tmp_path)
        lg.log_user_action("send_request_started", ip="192.168.1.1")
        content = (tmp_path / "test_logger.log").read_text()
        assert "send_request_started" in content

    def test_log_application_event_includes_event(self, tmp_path):
        lg = _make_logger(tmp_path)
        lg.log_application_event("application_started")
        content = (tmp_path / "test_logger.log").read_text()
        assert "application_started" in content


# ---------------------------------------------------------------------------
# JsonFormatter
# ---------------------------------------------------------------------------

class TestJsonFormatter:
    """JsonFormatter must produce valid JSON with the expected top-level keys."""

    def _make_record(self, message: str, level: int = logging.INFO) -> logging.LogRecord:
        record = logging.LogRecord(
            name="test", level=level, pathname="", lineno=0,
            msg=message, args=(), exc_info=None,
        )
        return record

    def test_output_is_valid_json(self):
        fmt = JsonFormatter()
        record = self._make_record("hello")
        output = fmt.format(record)
        parsed = json.loads(output)  # raises if not valid JSON
        assert isinstance(parsed, dict)

    def test_contains_timestamp(self):
        fmt = JsonFormatter()
        parsed = json.loads(fmt.format(self._make_record("x")))
        assert "timestamp" in parsed

    def test_contains_level(self):
        fmt = JsonFormatter()
        parsed = json.loads(fmt.format(self._make_record("x", logging.ERROR)))
        assert parsed["level"] == "ERROR"

    def test_contains_message(self):
        fmt = JsonFormatter()
        parsed = json.loads(fmt.format(self._make_record("my message")))
        assert parsed["message"] == "my message"

    def test_contains_logger_name(self):
        fmt = JsonFormatter()
        record = self._make_record("x")
        record.name = "preset_manager"
        parsed = json.loads(fmt.format(record))
        assert parsed["logger"] == "preset_manager"

    def test_includes_exception_when_exc_info_present(self):
        # Covers the `if record.exc_info` branch (line 150)
        fmt = JsonFormatter()
        try:
            raise RuntimeError("test error")
        except RuntimeError:
            import sys
            record = logging.LogRecord(
                name="t", level=logging.ERROR, pathname="", lineno=0,
                msg="oops", args=(), exc_info=sys.exc_info(),
            )
        parsed = json.loads(fmt.format(record))
        assert "exception" in parsed
        assert "RuntimeError" in parsed["exception"]

    def test_includes_stack_info_when_present(self):
        # Covers the `if record.stack_info` branch (line 152)
        fmt = JsonFormatter()
        record = logging.LogRecord(
            name="t", level=logging.DEBUG, pathname="", lineno=0,
            msg="stack", args=(), exc_info=None,
        )
        record.stack_info = "Stack trace here"
        parsed = json.loads(fmt.format(record))
        assert parsed["stack_trace"] == "Stack trace here"


# ---------------------------------------------------------------------------
# ColoredFormatter
# ---------------------------------------------------------------------------

class TestColoredFormatter:
    def test_output_contains_message(self):
        fmt = ColoredFormatter("%(levelname)s %(message)s")
        record = logging.LogRecord(
            name="t", level=logging.INFO, pathname="", lineno=0,
            msg="colortest", args=(), exc_info=None,
        )
        output = fmt.format(record)
        assert "colortest" in output

    def test_levelname_contains_ansi_reset(self):
        fmt = ColoredFormatter("%(levelname)s")
        record = logging.LogRecord(
            name="t", level=logging.WARNING, pathname="", lineno=0,
            msg="", args=(), exc_info=None,
        )
        output = fmt.format(record)
        # ANSI reset code must be present after the level name
        assert "\033[0m" in output


# ---------------------------------------------------------------------------
# LoggingManager
# ---------------------------------------------------------------------------

class TestLoggingManager:
    def test_get_logger_returns_structured_logger(self):
        mgr = LoggingManager()
        lg = mgr.get_logger("mgr_test")
        assert isinstance(lg, StructuredLogger)

    def test_get_logger_same_name_returns_same_instance(self):
        mgr = LoggingManager()
        lg1 = mgr.get_logger("shared")
        lg2 = mgr.get_logger("shared")
        assert lg1 is lg2

    def test_get_logger_different_names_are_different(self):
        mgr = LoggingManager()
        assert mgr.get_logger("a") is not mgr.get_logger("b")

    def test_set_global_level_does_not_raise(self):
        mgr = LoggingManager()
        mgr.get_logger("lvl_test")
        mgr.set_global_level("WARNING")  # must not raise

    def test_cleanup_closes_handlers(self):
        mgr = LoggingManager()
        mgr.get_logger("cleanup_test")
        mgr.cleanup()  # must not raise
        # After cleanup the internal logger list is unchanged but handlers are closed
        for lg in mgr.loggers.values():
            assert lg.logger.handlers == []


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

class TestModuleFunctions:
    def test_get_logger_returns_structured_logger(self):
        lg = get_logger("module_fn_test")
        assert isinstance(lg, StructuredLogger)

    def test_set_logging_level_does_not_raise(self):
        set_logging_level("DEBUG")  # must not raise

    def test_cleanup_logging_does_not_raise(self):
        cleanup_logging()  # must not raise

