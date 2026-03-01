"""Tests for resize operations."""

import pytest
from PIL import Image

from image_editor.operations.resize import resize, resize_to_preset, resize_file
from image_editor.operations.crop import PRESET_SIZES


def test_resize_explicit_dimensions(sample_rgb_image):
    result = resize(sample_rgb_image, 200, 150)
    assert result.size == (200, 150)


def test_resize_auto_height(sample_rgb_image):
    # 100x100 image, resize width to 50 -> height auto
    result = resize(sample_rgb_image, 50, 0)
    assert result.size[0] == 50
    assert result.size[1] == 50  # aspect ratio preserved


def test_resize_auto_width(sample_rgb_image):
    # 100x100 image, resize height to 200 -> width auto
    result = resize(sample_rgb_image, 0, 200)
    assert result.size[1] == 200
    assert result.size[0] == 200


def test_resize_keep_aspect(sample_rgb_image):
    # Fit 100x100 into 200x100; keep_aspect -> 100x100
    result = resize(sample_rgb_image, 200, 100, keep_aspect=True)
    assert result.size[1] <= 100
    assert result.size[0] <= 200


def test_resize_invalid_dimensions(sample_rgb_image):
    with pytest.raises(ValueError):
        resize(sample_rgb_image, 0, 0)


def test_resize_to_preset(sample_rgb_image):
    result = resize_to_preset(sample_rgb_image, "passport")
    assert result.size == PRESET_SIZES["passport"]


def test_resize_to_preset_with_aspect(sample_rgb_image):
    result = resize_to_preset(sample_rgb_image, "instagram_square", keep_aspect=True)
    # Should be padded to preset size
    assert result.size == PRESET_SIZES["instagram_square"]


def test_resize_to_unknown_preset(sample_rgb_image):
    with pytest.raises(ValueError, match="Unknown preset"):
        resize_to_preset(sample_rgb_image, "nonexistent_preset")


def test_resize_file(tmp_path, tmp_image_file):
    output = str(tmp_path / "resized.png")
    resize_file(tmp_image_file, output, 50, 50)
    with Image.open(output) as img:
        assert img.size == (50, 50)


def test_resize_file_with_preset(tmp_path, tmp_image_file):
    output = str(tmp_path / "resized_passport.png")
    resize_file(tmp_image_file, output, 0, 0, preset="passport")
    with Image.open(output) as img:
        assert img.size == PRESET_SIZES["passport"]
