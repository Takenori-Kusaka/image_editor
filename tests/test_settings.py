"""Unit tests for settings management."""

import json
import pytest
from pathlib import Path

from image_editor.settings import Settings, DEFAULTS


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


def test_defaults_populated():
    s = Settings.load.__func__(Settings, None)  # load without a file
    # Should have at least the default keys
    for key in DEFAULTS:
        assert key in s.as_dict()


def test_load_nonexistent_returns_defaults(tmp_path):
    path = tmp_path / "nonexistent.json"
    s = Settings.load(path)
    assert s.get("jpeg_quality") == DEFAULTS["jpeg_quality"]


def test_load_existing_file(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text(json.dumps({"jpeg_quality": 80, "backup_enabled": True}), encoding="utf-8")
    s = Settings.load(p)
    assert s.get("jpeg_quality") == 80
    assert s.get("backup_enabled") is True


def test_load_corrupted_file_falls_back_to_defaults(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text("NOT JSON", encoding="utf-8")
    s = Settings.load(p)
    assert s.get("jpeg_quality") == DEFAULTS["jpeg_quality"]


def test_load_non_dict_json_falls_back_to_defaults(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text("[1, 2, 3]", encoding="utf-8")
    s = Settings.load(p)
    assert s.get("jpeg_quality") == DEFAULTS["jpeg_quality"]


# ---------------------------------------------------------------------------
# get / set / update
# ---------------------------------------------------------------------------


def test_get_existing_key():
    s = Settings.from_dict({"jpeg_quality": 70})
    assert s.get("jpeg_quality") == 70


def test_get_missing_key_returns_default_param():
    s = Settings.from_dict({})
    assert s.get("no_such_key", "fallback") == "fallback"


def test_set_and_get():
    s = Settings.from_dict({})
    s.set("jpeg_quality", 60)
    assert s.get("jpeg_quality") == 60


def test_update_bulk():
    s = Settings.from_dict({})
    s.update({"jpeg_quality": 50, "bg_threshold": 40})
    assert s.get("jpeg_quality") == 50
    assert s.get("bg_threshold") == 40


def test_as_dict_is_copy():
    s = Settings.from_dict({"x": 1})
    d = s.as_dict()
    d["x"] = 99
    assert s.get("x") == 1  # original unchanged


# ---------------------------------------------------------------------------
# Save / persist
# ---------------------------------------------------------------------------


def test_save_creates_file(tmp_path):
    p = tmp_path / "out.json"
    s = Settings.from_dict({"jpeg_quality": 75})
    s.save(p)
    assert p.exists()
    data = json.loads(p.read_text())
    assert data["jpeg_quality"] == 75


def test_save_creates_parent_dirs(tmp_path):
    p = tmp_path / "sub" / "dir" / "settings.json"
    s = Settings.from_dict({})
    s.save(p)
    assert p.exists()


def test_load_save_round_trip(tmp_path):
    p = tmp_path / "settings.json"
    s1 = Settings.from_dict({"jpeg_quality": 42, "bg_method": "grabcut"})
    s1.save(p)

    s2 = Settings.load(p)
    assert s2.get("jpeg_quality") == 42
    assert s2.get("bg_method") == "grabcut"


# ---------------------------------------------------------------------------
# merged_with_options
# ---------------------------------------------------------------------------


def test_merged_with_options_overrides():
    s = Settings.from_dict({"jpeg_quality": 80})
    merged = s.merged_with_options(jpeg_quality=60)
    assert merged.get("jpeg_quality") == 60
    # Original unchanged
    assert s.get("jpeg_quality") == 80


def test_merged_with_options_none_does_not_override():
    s = Settings.from_dict({"jpeg_quality": 80})
    merged = s.merged_with_options(jpeg_quality=None)
    assert merged.get("jpeg_quality") == 80


# ---------------------------------------------------------------------------
# path property
# ---------------------------------------------------------------------------


def test_path_property_none_for_from_dict():
    s = Settings.from_dict({})
    assert s.path is None


def test_path_property_set_after_load(tmp_path):
    p = tmp_path / "s.json"
    p.write_text("{}", encoding="utf-8")
    s = Settings.load(p)
    assert s.path == p
