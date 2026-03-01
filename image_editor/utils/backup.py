"""Backup utilities for image_editor."""

import shutil
from datetime import datetime
from pathlib import Path


def create_backup(file_path: str, backup_dir: str = None) -> str:
    """Create a backup of a file before processing.

    Args:
        file_path: Path to the file to back up.
        backup_dir: Directory to store backups. Defaults to a 'backup' folder
                    next to the original file.

    Returns:
        Path to the backup file.
    """
    source = Path(file_path)
    if not source.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if backup_dir is None:
        backup_dir = source.parent / "backup"
    else:
        backup_dir = Path(backup_dir)

    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{source.stem}_{timestamp}{source.suffix}"
    backup_path = backup_dir / backup_name

    shutil.copy2(str(source), str(backup_path))
    return str(backup_path)


def create_backups(file_paths: list, backup_dir: str = None) -> list:
    """Create backups of multiple files.

    Args:
        file_paths: List of file paths to back up.
        backup_dir: Directory to store backups.

    Returns:
        List of backup file paths.
    """
    return [create_backup(fp, backup_dir) for fp in file_paths]
