"""Preset manager for API Test Tool."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config.constants import PRESETS_FILE
from config.logging_system import get_logger

_logger = get_logger("preset_manager")


class PresetManager:
    """Manages loading, saving, and querying test presets from a JSON file."""

    def __init__(self, presets_file: Path | None = None) -> None:
        """Initialise the manager and load existing presets from disk.

        :param presets_file: Path to the presets JSON file.  Defaults to
            ``PRESETS_FILE`` when ``None``.
        """
        self._file = presets_file if presets_file is not None else PRESETS_FILE
        self.presets: list[dict[str, Any]] = []
        self.load_presets()

    def load_presets(self) -> None:
        """Load presets from the JSON file into :attr:`presets`."""
        if not self._file.exists():
            self.presets = []
            return
        try:
            with self._file.open("r", encoding="utf-8") as f:
                self.presets = json.load(f)
        except Exception as exc:
            _logger.error("Failed to load presets", error=str(exc))
            self.presets = []

    def save_presets(self) -> None:
        """Persist the current :attr:`presets` list to disk."""
        try:
            with self._file.open("w", encoding="utf-8") as f:
                json.dump(self.presets, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            _logger.error("Failed to save presets", error=str(exc))

    def add_preset(self, preset: dict[str, Any]) -> None:
        """Add *preset* to the list, replacing any existing entry with the same name.

        :param preset: Preset dict; must contain a ``"name"`` key.
        """
        name = preset.get("name")
        if not name:
            return
        existing = self.get_by_name(name)
        if existing:
            self.presets.remove(existing)
        self.presets.append(preset)
        self.save_presets()

    def get_by_name(self, name: str) -> dict[str, Any] | None:
        """Return the first preset whose ``"name"`` matches *name*, or ``None``.

        :param name: Preset name to look up.
        :returns: Matching preset dict, or ``None`` if not found.
        """
        return next((p for p in self.presets if p.get("name") == name), None)

    def get_names(self) -> list[str]:
        """Return a list of all preset names in insertion order.

        :returns: List of preset name strings.
        """
        return [p.get("name", "") for p in self.presets]

    def delete_preset(self, name: str) -> bool:
        """Remove the preset named *name* and persist the change.

        :param name: Name of the preset to remove.
        :returns: ``True`` if the preset was found and removed, ``False`` otherwise.
        """
        existing = self.get_by_name(name)
        if existing:
            self.presets.remove(existing)
            self.save_presets()
            return True
        return False
