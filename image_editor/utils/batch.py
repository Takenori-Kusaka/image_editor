"""Batch processing utilities for image_editor."""

import os
from pathlib import Path
from typing import Callable, List, Optional


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".tif", ".ico"}


def find_images(directory: str, recursive: bool = False) -> List[str]:
    """Find all image files in a directory.

    Args:
        directory: Directory to search.
        recursive: If True, search subdirectories recursively.

    Returns:
        List of image file paths.
    """
    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    if recursive:
        files = dir_path.rglob("*")
    else:
        files = dir_path.glob("*")

    return [
        str(f) for f in sorted(files)
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ]


def batch_process(
    input_paths: List[str],
    process_func: Callable,
    output_dir: str = None,
    output_suffix: str = "",
    output_format: str = None,
    backup: bool = False,
    backup_dir: str = None,
    overwrite: bool = False,
    **kwargs,
) -> List[dict]:
    """Process multiple image files with a given function.

    Args:
        input_paths: List of input file paths.
        process_func: Function to apply to each file. Must accept
                      (input_path, output_path, **kwargs).
        output_dir: Directory for output files. Defaults to same as input.
        output_suffix: Suffix to add to output filename (before extension).
        output_format: Output format extension (e.g., 'png'). If None, keep original.
        backup: If True, create backup of original files before processing.
        backup_dir: Directory for backups.
        overwrite: If True, overwrite existing output files.
        **kwargs: Additional keyword arguments passed to process_func.

    Returns:
        List of dicts with 'input', 'output', 'backup', and 'status' keys.
    """
    if backup:
        from image_editor.utils.backup import create_backup

    results = []

    for input_path in input_paths:
        input_file = Path(input_path)
        result = {"input": str(input_path), "output": None, "backup": None, "status": "ok"}

        try:
            # Determine output path
            if output_dir:
                out_dir = Path(output_dir)
                out_dir.mkdir(parents=True, exist_ok=True)
            else:
                out_dir = input_file.parent

            if output_format:
                out_ext = f".{output_format.lstrip('.')}"
            else:
                out_ext = input_file.suffix

            out_name = f"{input_file.stem}{output_suffix}{out_ext}"
            output_path = out_dir / out_name

            if output_path.exists() and not overwrite:
                result["status"] = "skipped (output exists)"
                result["output"] = str(output_path)
                results.append(result)
                continue

            # Create backup if requested
            if backup:
                result["backup"] = create_backup(input_path, backup_dir)

            # Process the file
            process_func(str(input_path), str(output_path), **kwargs)
            result["output"] = str(output_path)

        except Exception as exc:
            result["status"] = f"error: {exc}"

        results.append(result)

    return results
