"""Tests for batch processing utilities."""

import pytest
from pathlib import Path
from PIL import Image

from image_editor.utils.batch import find_images, batch_process, IMAGE_EXTENSIONS


@pytest.fixture
def image_dir(tmp_path):
    """Create a temp directory with sample images."""
    for i, fmt in enumerate(["png", "jpg", "webp"]):
        img = Image.new("RGB", (50, 50), color=(i * 80, 0, 0))
        img.save(str(tmp_path / f"img_{i}.{fmt}"))
    # Non-image file should be ignored
    (tmp_path / "notes.txt").write_text("not an image")
    return str(tmp_path)


def test_find_images_finds_images(image_dir):
    images = find_images(image_dir)
    assert len(images) == 3
    for path in images:
        assert Path(path).suffix.lower() in IMAGE_EXTENSIONS


def test_find_images_excludes_non_images(image_dir):
    images = find_images(image_dir)
    assert not any(p.endswith(".txt") for p in images)


def test_find_images_recursive(tmp_path):
    subdir = tmp_path / "sub"
    subdir.mkdir()
    img = Image.new("RGB", (10, 10), color=(0, 0, 0))
    img.save(str(subdir / "sub_img.png"))
    img.save(str(tmp_path / "root_img.png"))

    images_non_recursive = find_images(str(tmp_path), recursive=False)
    images_recursive = find_images(str(tmp_path), recursive=True)

    assert len(images_non_recursive) == 1
    assert len(images_recursive) == 2


def test_find_images_not_a_directory(tmp_path):
    with pytest.raises(NotADirectoryError):
        find_images(str(tmp_path / "no_such_dir"))


def test_batch_process_resize(tmp_path, image_dir):
    from image_editor.operations.resize import resize_file

    output_dir = str(tmp_path / "output")
    files = find_images(image_dir)
    results = batch_process(
        files,
        resize_file,
        output_dir=output_dir,
        width=20,
        height=20,
    )

    assert len(results) == 3
    for r in results:
        assert r["status"] == "ok"
        assert Path(r["output"]).exists()
        with Image.open(r["output"]) as img:
            assert img.size == (20, 20)


def test_batch_process_skips_existing(tmp_path, image_dir):
    from image_editor.operations.resize import resize_file

    output_dir = str(tmp_path / "output")
    files = find_images(image_dir)

    # First pass
    batch_process(files, resize_file, output_dir=output_dir, width=20, height=20)
    # Second pass without overwrite - should skip
    results2 = batch_process(files, resize_file, output_dir=output_dir, width=20, height=20)
    for r in results2:
        assert r["status"].startswith("skipped")


def test_batch_process_overwrite(tmp_path, image_dir):
    from image_editor.operations.resize import resize_file

    output_dir = str(tmp_path / "output")
    files = find_images(image_dir)

    batch_process(files, resize_file, output_dir=output_dir, width=20, height=20)
    results2 = batch_process(files, resize_file, output_dir=output_dir, width=30, height=30, overwrite=True)
    for r in results2:
        assert r["status"] == "ok"


def test_batch_process_with_backup(tmp_path, image_dir):
    from image_editor.operations.resize import resize_file

    output_dir = str(tmp_path / "output")
    backup_dir = str(tmp_path / "backups")
    files = find_images(image_dir)

    results = batch_process(
        files,
        resize_file,
        output_dir=output_dir,
        backup=True,
        backup_dir=backup_dir,
        overwrite=True,
        width=20,
        height=20,
    )

    for r in results:
        assert r["backup"] is not None
        assert Path(r["backup"]).exists()
