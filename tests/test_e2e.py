"""End-to-end tests that exercise the CLI as a whole.

These tests invoke the CLI through Click's test runner, simulating real
command-line usage including settings file loading.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from PIL import Image

from image_editor.cli import cli


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def png100(tmp_path):
    img = Image.new("RGB", (100, 100), color=(180, 90, 45))
    p = tmp_path / "source.png"
    img.save(str(p))
    return str(p)


@pytest.fixture
def white_bg_png(tmp_path):
    img = Image.new("RGB", (80, 80), color=(255, 255, 255))
    for x in range(30, 50):
        for y in range(30, 50):
            img.putpixel((x, y), (200, 50, 50))
    p = tmp_path / "white_bg.png"
    img.save(str(p))
    return str(p)


@pytest.fixture
def settings_file(tmp_path):
    """A settings JSON file with common defaults."""
    data = {
        "jpeg_quality": 80,
        "bg_threshold": 25,
        "backup_enabled": False,
    }
    p = tmp_path / "settings.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


# ---------------------------------------------------------------------------
# Global: --settings-file option
# ---------------------------------------------------------------------------


def test_settings_file_is_loaded(runner, tmp_path, png100, settings_file):
    """--settings-file path is accepted without error."""
    output = str(tmp_path / "out.jpg")
    result = runner.invoke(cli, [
        "--settings-file", settings_file,
        "convert", png100,
        "-o", output,
        "--format", "jpeg",
    ])
    assert result.exit_code == 0, result.output
    with Image.open(output) as img:
        assert img.format == "JPEG"


def test_settings_file_missing_ok(runner, tmp_path, png100):
    """A non-existent settings file path should fall back to defaults."""
    output = str(tmp_path / "out.jpg")
    result = runner.invoke(cli, [
        "--settings-file", str(tmp_path / "nonexistent.json"),
        "convert", png100,
        "-o", output,
        "--format", "jpeg",
    ])
    assert result.exit_code == 0, result.output


# ---------------------------------------------------------------------------
# Resize E2E
# ---------------------------------------------------------------------------


def test_e2e_resize_to_dimensions(runner, tmp_path, png100):
    output = str(tmp_path / "out.png")
    result = runner.invoke(cli, [
        "resize", png100, "-o", output,
        "--width", "50", "--height", "50",
    ])
    assert result.exit_code == 0, result.output
    with Image.open(output) as img:
        assert img.size == (50, 50)


def test_e2e_resize_keep_aspect(runner, tmp_path, png100):
    output = str(tmp_path / "out.png")
    result = runner.invoke(cli, [
        "resize", png100, "-o", output,
        "--width", "80", "--height", "80", "--keep-aspect",
    ])
    assert result.exit_code == 0, result.output
    with Image.open(output) as img:
        assert img.size[0] <= 80 and img.size[1] <= 80


def test_e2e_resize_preset_passport(runner, tmp_path, png100):
    output = str(tmp_path / "passport.png")
    result = runner.invoke(cli, [
        "resize", png100, "-o", output, "--preset", "passport",
    ])
    assert result.exit_code == 0, result.output
    with Image.open(output) as img:
        assert img.size == (413, 531)


# ---------------------------------------------------------------------------
# Crop E2E
# ---------------------------------------------------------------------------


def test_e2e_crop(runner, tmp_path, png100):
    output = str(tmp_path / "cropped.png")
    result = runner.invoke(cli, [
        "crop", png100, "-o", output,
        "--left", "10", "--top", "10", "--right", "60", "--bottom", "70",
    ])
    assert result.exit_code == 0, result.output
    with Image.open(output) as img:
        assert img.size == (50, 60)


# ---------------------------------------------------------------------------
# Convert E2E (WebP, SVG, JPEG)
# ---------------------------------------------------------------------------


def test_e2e_convert_to_webp(runner, tmp_path, png100):
    output = str(tmp_path / "out.webp")
    result = runner.invoke(cli, ["convert", png100, "-o", output])
    assert result.exit_code == 0, result.output
    with Image.open(output) as img:
        assert img.format == "WEBP"


def test_e2e_convert_to_svg(runner, tmp_path, png100):
    output = str(tmp_path / "out.svg")
    result = runner.invoke(cli, ["convert", png100, "-o", output, "--format", "svg"])
    assert result.exit_code == 0, result.output
    content = Path(output).read_text(encoding="utf-8")
    assert "<svg" in content
    assert "data:image" in content


def test_e2e_convert_to_jpeg_with_quality(runner, tmp_path, png100):
    output = str(tmp_path / "out.jpg")
    result = runner.invoke(cli, [
        "convert", png100, "-o", output, "--format", "jpeg", "--quality", "60",
    ])
    assert result.exit_code == 0, result.output
    with Image.open(output) as img:
        assert img.format == "JPEG"


# ---------------------------------------------------------------------------
# Background E2E
# ---------------------------------------------------------------------------


def test_e2e_background_remove_flood(runner, tmp_path, white_bg_png):
    output = str(tmp_path / "transparent.png")
    result = runner.invoke(cli, [
        "background", white_bg_png, "-o", output,
        "--action", "remove", "--method", "flood", "--threshold", "30",
    ])
    assert result.exit_code == 0, result.output
    with Image.open(output) as img:
        assert img.mode == "RGBA"
        # Corner pixel should be transparent
        assert img.getpixel((0, 0))[3] == 0


def test_e2e_background_replace(runner, tmp_path, white_bg_png):
    output = str(tmp_path / "blue_bg.png")
    result = runner.invoke(cli, [
        "background", white_bg_png, "-o", output,
        "--action", "replace", "--color", "0,0,200",
    ])
    assert result.exit_code == 0, result.output
    with Image.open(output) as img:
        r, g, b = img.getpixel((0, 0))
        assert b > 150


def test_e2e_background_grabcut(runner, tmp_path, png100):
    output = str(tmp_path / "grabcut.png")
    result = runner.invoke(cli, [
        "background", png100, "-o", output,
        "--action", "remove", "--method", "grabcut", "--grabcut-iterations", "2",
    ])
    assert result.exit_code == 0, result.output
    with Image.open(output) as img:
        assert img.mode == "RGBA"


# ---------------------------------------------------------------------------
# Face E2E
# ---------------------------------------------------------------------------


def test_e2e_face_no_face_exits_with_error(runner, tmp_path, png100):
    """Solid-colour image has no face; CLI should exit with an error message."""
    output = str(tmp_path / "face.png")
    result = runner.invoke(cli, [
        "face", png100, "-o", output, "--style", "real",
    ])
    assert result.exit_code != 0 or "No face detected" in result.output


def test_e2e_face_with_mocked_detection(runner, tmp_path, png100, monkeypatch):
    """Monkeypatch detect_faces to verify the face command saves output."""
    import image_editor.operations.face as face_module

    def _mock_detect(image, **kwargs):
        return [(10, 10, 40, 40)]

    monkeypatch.setattr(face_module, "detect_faces", _mock_detect)

    output = str(tmp_path / "face.png")
    result = runner.invoke(cli, [
        "face", png100, "-o", output, "--style", "real", "--padding", "0.1",
    ])
    assert result.exit_code == 0, result.output
    assert Path(output).exists()


# ---------------------------------------------------------------------------
# Batch E2E
# ---------------------------------------------------------------------------


def test_e2e_batch_resize(runner, tmp_path):
    in_dir = tmp_path / "input"
    in_dir.mkdir()
    for i in range(3):
        Image.new("RGB", (100, 100), (i * 80, 0, 0)).save(str(in_dir / f"img_{i}.png"))

    out_dir = str(tmp_path / "output")
    result = runner.invoke(cli, [
        "batch", "resize", str(in_dir), "-o", out_dir,
        "--width", "40", "--height", "40",
    ])
    assert result.exit_code == 0, result.output
    assert "3 processed" in result.output


def test_e2e_batch_convert_webp(runner, tmp_path):
    in_dir = tmp_path / "input"
    in_dir.mkdir()
    for i in range(2):
        Image.new("RGB", (50, 50), (0, i * 100, 0)).save(str(in_dir / f"img_{i}.png"))

    out_dir = str(tmp_path / "output")
    result = runner.invoke(cli, [
        "batch", "convert", str(in_dir), "-o", out_dir, "--format", "webp",
    ])
    assert result.exit_code == 0, result.output
    assert "2 processed" in result.output


def test_e2e_batch_background_remove(runner, tmp_path):
    in_dir = tmp_path / "input"
    in_dir.mkdir()
    for i in range(2):
        img = Image.new("RGB", (60, 60), color=(255, 255, 255))
        for x in range(20, 40):
            for y in range(20, 40):
                img.putpixel((x, y), (i * 100, 50, 50))
        img.save(str(in_dir / f"img_{i}.png"))

    out_dir = str(tmp_path / "output")
    result = runner.invoke(cli, [
        "batch", "background", str(in_dir), "-o", out_dir,
        "--action", "remove",
    ])
    assert result.exit_code == 0, result.output
    assert "2 processed" in result.output


# ---------------------------------------------------------------------------
# Settings file integration (CLI reads defaults from file)
# ---------------------------------------------------------------------------


def test_e2e_settings_file_backup_disabled(runner, tmp_path, png100, settings_file):
    """backup_enabled=False in settings → no backup created."""
    output = str(tmp_path / "out.png")
    result = runner.invoke(cli, [
        "--settings-file", settings_file,
        "crop", png100, "-o", output,
        "--right", "50", "--bottom", "50",
    ])
    assert result.exit_code == 0, result.output
    # No backup directory should have been created
    backup_dir = Path(png100).parent / "backup"
    assert not backup_dir.exists()
