"""Dependency injection container and Protocol interfaces for API Test Tool."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

# ── Protocols ─────────────────────────────────────────────────────────────────

@runtime_checkable
class PresetManagerProtocol(Protocol):
    """Structural interface for preset managers."""

    presets: list[dict[str, Any]]

    def load_presets(self) -> list[dict[str, Any]]: ...
    def save_presets(self, presets: list[dict[str, Any]]) -> None: ...
    def add_preset(self, preset: dict[str, Any]) -> None: ...
    def get_by_name(self, name: str) -> dict[str, Any] | None: ...
    def delete_preset(self, name: str) -> bool: ...


@runtime_checkable
class RequestManagerProtocol(Protocol):
    """Structural interface for request managers."""

    def send_request_async(
        self,
        ip: str,
        user: str,
        password: bytearray,
        endpoint: str,
        json_file: str,
        simple_format: bool,
        json_type: str,
        callback: Callable[..., Any],
        preset_name: str = "",
        log_file: Path | None = None,
    ) -> Any: ...

    def build_request(
        self,
        ip: str,
        endpoint: str,
        json_file: str,
        simple_format: bool,
    ) -> tuple[str, str]: ...

    def start_new_log(self, preset_name: str) -> Path: ...


@runtime_checkable
class SettingsManagerProtocol(Protocol):
    """Structural interface for settings managers."""

    def load_settings(self) -> None: ...
    def save_settings(self) -> None: ...
    def get_last_ip(self) -> str: ...
    def set_last_ip(self, ip: str) -> None: ...
    def get_last_user(self) -> str: ...
    def set_last_user(self, user: str) -> None: ...
    def get_last_simple_format(self) -> bool: ...
    def set_last_simple_format(self, simple: bool) -> None: ...
    def get_last_test_mode(self) -> str: ...
    def set_last_test_mode(self, mode: str) -> None: ...
    def get_last_json_type(self) -> str: ...
    def set_last_json_type(self, json_type: str) -> None: ...
    def get_last_endpoint(self) -> str: ...
    def set_last_endpoint(self, endpoint: str) -> None: ...
    def get_last_json_file(self) -> str: ...
    def set_last_json_file(self, json_file: str) -> None: ...
    def get_window_geometry(self) -> str: ...
    def set_window_geometry(self, geometry: str) -> None: ...


# ── DI Container ──────────────────────────────────────────────────────────────

class DIContainer:
    """Lightweight dependency injection container.

    Services are registered by name with an optional singleton flag.  When
    ``singleton=True`` the factory is called only once; subsequent calls to
    :meth:`get` return the cached instance.
    """

    def __init__(self) -> None:
        self._services: dict[str, dict[str, Any]] = {}
        self._singletons: dict[str, Any] = {}

    def register(
        self,
        name: str,
        factory: Callable[[], Any],
        singleton: bool = False,
    ) -> None:
        """Register a service factory under *name*.

        :param name: Unique service identifier.
        :param factory: Zero-argument callable that creates the service instance.
        :param singleton: When True the instance is cached after the first call.
        """
        self._services[name] = {"factory": factory, "singleton": singleton}

    def get(self, name: str) -> Any:
        """Resolve and return the service registered under *name*.

        :param name: Service identifier previously passed to :meth:`register`.
        :raises ValueError: If *name* has not been registered.
        """
        if name not in self._services:
            raise ValueError(f"Service '{name}' not registered")
        service = self._services[name]
        if service["singleton"]:
            if name not in self._singletons:
                self._singletons[name] = service["factory"]()
            return self._singletons[name]
        return service["factory"]()

    def register_defaults(self) -> None:
        """Register the three default application services as singletons."""
        from managers.presets import PresetManager
        from managers.requests_manager import RequestManager
        from managers.settings import SettingsManager

        self.register("preset_manager", lambda: PresetManager(), singleton=True)
        self.register("request_manager", lambda: RequestManager(), singleton=True)
        self.register("settings_manager", lambda: SettingsManager(), singleton=True)


_container = DIContainer()
_container.register_defaults()


def get_container() -> DIContainer:
    """Return the module-level singleton :class:`DIContainer`."""
    return _container


def resolve(service_name: str) -> Any:
    """Shorthand to resolve *service_name* from the global container."""
    return _container.get(service_name)
