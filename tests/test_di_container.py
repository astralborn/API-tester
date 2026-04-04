"""Tests for config/di_container.py — DIContainer and protocols."""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from config.di_container import (
    DIContainer,
    PresetManagerProtocol,
    RequestManagerProtocol,
    SettingsManagerProtocol,
    get_container,
    resolve,
)


# ---------------------------------------------------------------------------
# DIContainer — register / get
# ---------------------------------------------------------------------------

class TestDIContainer:
    def test_get_unregistered_raises(self):
        c = DIContainer()
        with pytest.raises(ValueError, match="not registered"):
            c.get("nonexistent")

    def test_register_and_get_transient(self):
        c = DIContainer()
        c.register("counter", lambda: object())
        obj1 = c.get("counter")
        obj2 = c.get("counter")
        # transient: new instance each time
        assert obj1 is not obj2

    def test_register_singleton_returns_same_instance(self):
        c = DIContainer()
        c.register("singleton_svc", lambda: object(), singleton=True)
        obj1 = c.get("singleton_svc")
        obj2 = c.get("singleton_svc")
        assert obj1 is obj2

    def test_register_defaults_adds_all_services(self):

        c = DIContainer()
        with (
            patch("managers.presets.PRESETS_FILE", MagicMock(exists=lambda: False)),
            patch("config.constants.resource_path", return_value=MagicMock(
                exists=lambda: False, mkdir=lambda **_: None, open=MagicMock()
            )),
        ):
            c.register_defaults()

        for name in ("preset_manager", "request_manager", "settings_manager"):
            assert name in c._services

    def test_factory_called_on_get(self):
        c = DIContainer()
        factory = MagicMock(return_value=42)
        c.register("svc", factory)
        result = c.get("svc")
        assert result == 42
        factory.assert_called_once()

    def test_singleton_factory_called_once(self):
        c = DIContainer()
        factory = MagicMock(side_effect=lambda: object())
        c.register("svc", factory, singleton=True)
        c.get("svc")
        c.get("svc")
        assert factory.call_count == 1


# ---------------------------------------------------------------------------
# Protocol structural checks
# ---------------------------------------------------------------------------

class TestPresetManagerProtocol:
    def test_mock_satisfies_protocol(self):
        class Stub:
            def load_presets(self): ...
            def save_presets(self, presets): ...
            def add_preset(self, preset): ...
            def get_by_name(self, name): ...
            def delete_preset(self, name): ...
        assert isinstance(Stub(), PresetManagerProtocol)

    def test_object_missing_methods_does_not_satisfy(self):
        class Incomplete:
            def load_presets(self): ...
        assert not isinstance(Incomplete(), PresetManagerProtocol)


class TestRequestManagerProtocol:
    def test_mock_satisfies_protocol(self):
        class Stub:
            def send_request_async(self, ip, user, password, endpoint,
                                   json_file, simple_format, json_type,
                                   callback, preset_name=""): ...
            def build_request(self, ip, endpoint, json_file, simple_format): ...
        assert isinstance(Stub(), RequestManagerProtocol)


class TestSettingsManagerProtocol:
    def test_mock_satisfies_protocol(self):
        class Stub:
            def load_settings(self): ...
            def save_settings(self): ...
            def get_last_ip(self): ...
            def set_last_ip(self, ip): ...
            def get_last_user(self): ...
            def set_last_user(self, user): ...
            def get_window_geometry(self): ...
            def set_window_geometry(self, geometry): ...
        assert isinstance(Stub(), SettingsManagerProtocol)


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

class TestModuleFunctions:
    def test_get_container_returns_di_container(self):
        # get_container() returns the module-level singleton DIContainer
        c = get_container()
        assert isinstance(c, DIContainer)

    def test_get_container_returns_same_instance(self):
        # Always the same object — it is a module-level singleton
        assert get_container() is get_container()

    def test_resolve_returns_registered_service(self):
        # resolve() is a shortcut for get_container().get(name).
        # The default container pre-registers preset_manager, request_manager,
        # and settings_manager, so resolving any of them must not raise.
        from managers.presets import PresetManager
        result = resolve("preset_manager")
        assert isinstance(result, PresetManager)


