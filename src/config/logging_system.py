"""Structured logging system for API Test Tool.

Provides :class:`StructuredLogger` — a thin wrapper around the standard
``logging`` module that writes three simultaneous output streams:

* **Plain-text rotating file** — human-readable, DEBUG+.
* **Structured JSONL rotating file** — machine-readable, DEBUG+.
* **Error-only rotating file** — ERROR+ with exception details.
* **Coloured console** — INFO+.
"""
from __future__ import annotations

import json
import logging
import logging.handlers
from datetime import datetime
from typing import Any, ClassVar

from config.constants import resource_path

# ── Structured Logger ─────────────────────────────────────────────────────────

class StructuredLogger:
    """Enhanced logger with structured output and file rotation."""

    def __init__(self, name: str = "api_tester", log_dir: str = "logs") -> None:
        """Initialise the logger and attach all handlers.

        :param name: Logger name (used as the log-file prefix).
        :param log_dir: Directory path relative to the ``src/`` root.
        """
        self.name = name
        self.log_dir = resource_path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        self._setup_console_handler()
        self._setup_file_handler()
        self._setup_json_handler()
        self._setup_error_handler()

    def _setup_console_handler(self) -> None:
        """Attach a coloured INFO-level console handler."""
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        handler.setFormatter(ColoredFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        self.logger.addHandler(handler)

    def _setup_file_handler(self) -> None:
        """Attach a rotating plain-text DEBUG-level file handler."""
        handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.name}.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s"
            " - %(funcName)s:%(lineno)d - %(message)s"
        ))
        self.logger.addHandler(handler)

    def _setup_json_handler(self) -> None:
        """Attach a rotating JSONL DEBUG-level structured handler."""
        handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.name}_structured.jsonl",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)

    def _setup_error_handler(self) -> None:
        """Attach a rotating ERROR-level file handler with exception details."""
        handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.name}_errors.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setLevel(logging.ERROR)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s"
            " - %(funcName)s:%(lineno)d - %(message)s\n"
            "Exception: %(exc_info)s\n---"
        ))
        self.logger.addHandler(handler)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log *message* at DEBUG level with optional structured fields."""
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log *message* at INFO level with optional structured fields."""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log *message* at WARNING level with optional structured fields."""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log *message* at ERROR level with optional structured fields."""
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log *message* at CRITICAL level with optional structured fields."""
        self.logger.critical(message, extra=kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log *message* at ERROR level including the current exception info."""
        self.logger.exception(message, extra=kwargs)

    def log_request(
        self,
        method: str,
        url: str,
        status_code: int,
        response_time: float,
        **kwargs: Any,
    ) -> None:
        """Log an HTTP request/response pair at INFO level.

        :param method: HTTP method (e.g. ``"POST"``).
        :param url: Full request URL.
        :param status_code: HTTP response status code.
        :param response_time: Round-trip duration in seconds.
        :param kwargs: Additional structured fields to include in the log entry.
        """
        self.info(
            f"HTTP {method} {url} - {status_code} - {response_time:.3f}s",
            request_method=method,
            request_url=url,
            response_status=status_code,
            response_time=response_time,
            **kwargs,
        )

    def log_preset_action(self, action: str, preset_name: str, **kwargs: Any) -> None:
        """Log a preset lifecycle event at INFO level.

        :param action: Action label (e.g. ``"load_started"``).
        :param preset_name: Name of the affected preset.
        :param kwargs: Additional structured fields.
        """
        self.info(
            f"Preset {action}: {preset_name}",
            action=action,
            preset_name=preset_name,
            **kwargs,
        )

    def log_user_action(self, action: str, **kwargs: Any) -> None:
        """Log a user-initiated action at DEBUG level.

        :param action: Short action identifier (e.g. ``"send_request_started"``).
        :param kwargs: Additional structured fields.
        """
        self.debug(f"User action: {action}", user_action=action, **kwargs)

    def log_application_event(self, event: str, **kwargs: Any) -> None:
        """Log an application lifecycle event at INFO level.

        :param event: Event identifier (e.g. ``"application_started"``).
        :param kwargs: Additional structured fields.
        """
        self.info(f"Application event: {event}", app_event=event, **kwargs)


# ── Custom Formatters ─────────────────────────────────────────────────────────

class ColoredFormatter(logging.Formatter):
    """Logging formatter that prepends ANSI colour codes to the level name."""

    COLORS: ClassVar[dict[str, str]] = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET: ClassVar[str] = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Colour the level name then delegate to the standard formatter."""
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class JsonFormatter(logging.Formatter):
    """Logging formatter that serialises each record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        """Return a JSON string representing *record*."""
        entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            entry["stack_trace"] = record.stack_info

        _skip = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "lineno", "funcName", "created", "msecs",
            "relativeCreated", "thread", "threadName", "processName",
            "process", "getMessage", "exc_info", "exc_text", "stack_info",
            "taskName",
        }
        for key, value in record.__dict__.items():
            if key not in _skip:
                entry[key] = value

        return json.dumps(entry, default=str)


# ── Logging Manager ───────────────────────────────────────────────────────────

class LoggingManager:
    """Central registry that creates and caches :class:`StructuredLogger` instances."""

    def __init__(self) -> None:
        self.loggers: dict[str, StructuredLogger] = {}
        logging.getLogger().setLevel(logging.INFO)

    def get_logger(self, name: str) -> StructuredLogger:
        """Return the cached logger for *name*, creating it if necessary.

        :param name: Logger name used as the log-file prefix.
        """
        if name not in self.loggers:
            self.loggers[name] = StructuredLogger(name)
        return self.loggers[name]

    def set_global_level(self, level: str) -> None:
        """Set the root logger and all cached loggers to *level*.

        :param level: Level name accepted by :func:`logging.getLevelName`
            (e.g. ``"DEBUG"``, ``"INFO"``).
        """
        log_level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        for logger in self.loggers.values():
            logger.logger.setLevel(log_level)

    def cleanup(self) -> None:
        """Close and remove all handlers from every cached logger."""
        for logger in self.loggers.values():
            for handler in logger.logger.handlers:
                handler.close()
            logger.logger.handlers.clear()


_logging_manager = LoggingManager()


def get_logger(name: str = "api_tester") -> StructuredLogger:
    """Return a :class:`StructuredLogger` for *name* from the global manager."""
    return _logging_manager.get_logger(name)


def set_logging_level(level: str) -> None:
    """Set the global logging level via the module-level :class:`LoggingManager`."""
    _logging_manager.set_global_level(level)


def cleanup_logging() -> None:
    """Close all log handlers via the module-level :class:`LoggingManager`."""
    _logging_manager.cleanup()
