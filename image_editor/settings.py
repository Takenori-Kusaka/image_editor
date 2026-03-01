"""External settings management for image_editor.

Settings are stored as JSON and persist between sessions.
Default location: ~/.config/image_editor/settings.json

CLI usage:
    image-editor --settings settings.json resize ...

GUI: automatically loads/saves on open/close.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


# Default settings shipped with the tool
DEFAULTS: Dict[str, Any] = {
    "default_output_dir": None,
    "backup_enabled": False,
    "backup_dir": None,
    "jpeg_quality": 95,
    "bg_threshold": 30,
    "bg_method": "flood",          # "flood" | "grabcut"
    "face_padding": 0.2,
    "face_min_size": 30,
    "resize_keep_aspect": False,
    "last_input_path": None,
    "last_output_path": None,
    "last_input_dir": None,
    "last_output_dir": None,
}

_DEFAULT_CONFIG_PATH = Path.home() / ".config" / "image_editor" / "settings.json"


class Settings:
    """Load, access, and persist application settings.

    Settings are plain JSON key-value pairs. Unknown keys from the file are
    preserved so that future versions can extend the schema without data loss.

    Examples::

        # Load from the default location (creates defaults if missing)
        settings = Settings.load()
        quality = settings.get("jpeg_quality")

        # Load from an explicit file (useful for CLI --settings option)
        settings = Settings.load("my_settings.json")

        # Modify and save
        settings.set("jpeg_quality", 85)
        settings.save()
    """

    def __init__(self, data: Dict[str, Any], path: Optional[Path] = None):
        self._data: Dict[str, Any] = {**DEFAULTS, **data}
        self._path: Optional[Path] = path

    # ------------------------------------------------------------------
    # Class-level factories
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, path: Optional[str | Path] = None) -> "Settings":
        """Load settings from *path*, falling back to defaults.

        Args:
            path: Path to a JSON settings file. If *None*, the default
                  user-config location is used
                  (``~/.config/image_editor/settings.json``).

        Returns:
            A :class:`Settings` instance.
        """
        resolved = Path(path) if path else _DEFAULT_CONFIG_PATH
        data: Dict[str, Any] = {}
        if resolved.exists():
            try:
                with resolved.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if not isinstance(data, dict):
                    data = {}
            except (json.JSONDecodeError, OSError):
                data = {}
        return cls(data, resolved)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """Create a :class:`Settings` instance from a dictionary."""
        return cls(data, None)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value for *key*, or *default* if not set."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set *key* to *value* in the in-memory settings."""
        self._data[key] = value

    def update(self, data: Dict[str, Any]) -> None:
        """Bulk-update settings from a dictionary."""
        self._data.update(data)

    def as_dict(self) -> Dict[str, Any]:
        """Return a copy of the current settings as a plain dict."""
        return dict(self._data)

    @property
    def path(self) -> Optional[Path]:
        """Path this settings object will be saved to."""
        return self._path

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: Optional[str | Path] = None) -> Path:
        """Persist settings to *path* (or the path used when loading).

        The parent directory is created automatically.

        Args:
            path: Override save destination. If *None*, the path used when
                  loading is used. If that is also *None*, the default user
                  config path is used.

        Returns:
            The path the file was written to.
        """
        dest = Path(path) if path else (self._path or _DEFAULT_CONFIG_PATH)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2, ensure_ascii=False)
        self._path = dest
        return dest

    # ------------------------------------------------------------------
    # Helpers for CLI option merging
    # ------------------------------------------------------------------

    def merged_with_options(self, **options: Any) -> "Settings":
        """Return a *new* Settings with CLI option overrides applied.

        Only non-``None`` *options* values override the loaded settings.

        Args:
            **options: Keyword arguments representing CLI option values.

        Returns:
            A new :class:`Settings` instance with the overrides applied.
        """
        merged = dict(self._data)
        for key, value in options.items():
            if value is not None:
                merged[key] = value
        return Settings(merged, self._path)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Settings(path={self._path!r}, keys={list(self._data.keys())})"
