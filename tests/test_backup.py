"""Tests for backup utilities."""

import pytest
from pathlib import Path

from image_editor.utils.backup import create_backup, create_backups


def test_create_backup_creates_file(tmp_path, tmp_image_file):
    backup_dir = str(tmp_path / "backups")
    backup_path = create_backup(tmp_image_file, backup_dir)
    assert Path(backup_path).exists()


def test_create_backup_default_dir(tmp_path, tmp_image_file):
    # Should create a 'backup' folder next to the input file
    backup_path = create_backup(tmp_image_file)
    assert Path(backup_path).exists()
    assert "backup" in backup_path


def test_create_backup_filename_includes_timestamp(tmp_path, tmp_image_file):
    backup_path = create_backup(tmp_image_file)
    name = Path(backup_path).name
    # Should include original stem and a timestamp-like component
    assert "sample" in name


def test_create_backup_nonexistent_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        create_backup(str(tmp_path / "nonexistent.png"))


def test_create_backups_multiple_files(tmp_path):
    from PIL import Image
    files = []
    for i in range(3):
        p = tmp_path / f"img_{i}.png"
        Image.new("RGB", (10, 10), color=(i * 80, 0, 0)).save(str(p))
        files.append(str(p))

    backup_dir = str(tmp_path / "backups")
    backup_paths = create_backups(files, backup_dir)
    assert len(backup_paths) == 3
    for bp in backup_paths:
        assert Path(bp).exists()
