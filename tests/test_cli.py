"""Tests for CLI commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from PIL import Image

from image_editor.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def sample_png(tmp_path):
    img = Image.new("RGB", (100, 100), color=(255, 100, 0))
    path = tmp_path / "sample.png"
    img.save(str(path))
    return str(path)


@pytest.fixture
def white_bg_png(tmp_path):
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    for x in range(40, 60):
        for y in range(40, 60):
            img.putpixel((x, y), (255, 0, 0))
    path = tmp_path / "white_bg.png"
    img.save(str(path))
    return str(path)


def test_version(runner):
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_crop_command(runner, tmp_path, sample_png):
    output = str(tmp_path / "out.png")
    result = runner.invoke(cli, [
        "crop", sample_png,
        "-o", output,
        "--left", "0", "--top", "0", "--right", "50", "--bottom", "50",
    ])
    assert result.exit_code == 0, result.output
    with Image.open(output) as img:
        assert img.size == (50, 50)


def test_resize_command(runner, tmp_path, sample_png):
    output = str(tmp_path / "out.png")
    result = runner.invoke(cli, [
        "resize", sample_png,
        "-o", output,
        "--width", "200", "--height", "150",
    ])
    assert result.exit_code == 0, result.output
    with Image.open(output) as img:
        assert img.size == (200, 150)


def test_resize_command_preset(runner, tmp_path, sample_png):
    output = str(tmp_path / "out.png")
    result = runner.invoke(cli, [
        "resize", sample_png,
        "-o", output,
        "--preset", "passport",
    ])
    assert result.exit_code == 0, result.output
    with Image.open(output) as img:
        assert img.size == (413, 531)


def test_resize_command_no_dimensions(runner, tmp_path, sample_png):
    output = str(tmp_path / "out.png")
    result = runner.invoke(cli, ["resize", sample_png, "-o", output])
    assert result.exit_code != 0


def test_convert_command(runner, tmp_path, sample_png):
    output = str(tmp_path / "out.jpg")
    result = runner.invoke(cli, [
        "convert", sample_png,
        "-o", output,
        "--format", "jpeg",
    ])
    assert result.exit_code == 0, result.output
    with Image.open(output) as img:
        assert img.format == "JPEG"


def test_background_command_remove(runner, tmp_path, white_bg_png):
    output = str(tmp_path / "out.png")
    result = runner.invoke(cli, [
        "background", white_bg_png,
        "-o", output,
        "--action", "remove",
        "--threshold", "30",
    ])
    assert result.exit_code == 0, result.output
    with Image.open(output) as img:
        assert img.mode == "RGBA"
        r, g, b, a = img.getpixel((0, 0))
        assert a == 0  # background transparent


def test_background_command_replace(runner, tmp_path, white_bg_png):
    output = str(tmp_path / "out.png")
    result = runner.invoke(cli, [
        "background", white_bg_png,
        "-o", output,
        "--action", "replace",
        "--color", "0,0,255",
    ])
    assert result.exit_code == 0, result.output
    with Image.open(output) as img:
        r, g, b = img.getpixel((0, 0))
        assert b > 200


def test_crop_command_with_backup(runner, tmp_path, sample_png):
    output = str(tmp_path / "out.png")
    backup_dir = str(tmp_path / "bk")
    result = runner.invoke(cli, [
        "crop", sample_png,
        "-o", output,
        "--right", "50", "--bottom", "50",
        "--backup", "--backup-dir", backup_dir,
    ])
    assert result.exit_code == 0, result.output
    assert Path(backup_dir).exists()
    assert len(list(Path(backup_dir).iterdir())) == 1


def test_batch_resize_command(runner, tmp_path):
    # Create sample images
    in_dir = tmp_path / "input"
    in_dir.mkdir()
    out_dir = str(tmp_path / "output")
    for i in range(3):
        Image.new("RGB", (100, 100), color=(i * 80, 0, 0)).save(str(in_dir / f"img_{i}.png"))

    result = runner.invoke(cli, [
        "batch", "resize", str(in_dir),
        "-o", out_dir,
        "--width", "50", "--height", "50",
    ])
    assert result.exit_code == 0, result.output
    assert "3 processed" in result.output


def test_batch_convert_command(runner, tmp_path):
    in_dir = tmp_path / "input"
    in_dir.mkdir()
    out_dir = str(tmp_path / "output")
    for i in range(2):
        Image.new("RGB", (50, 50), color=(0, i * 100, 0)).save(str(in_dir / f"img_{i}.png"))

    result = runner.invoke(cli, [
        "batch", "convert", str(in_dir),
        "-o", out_dir,
        "--format", "jpg",
    ])
    assert result.exit_code == 0, result.output
    assert "2 processed" in result.output
