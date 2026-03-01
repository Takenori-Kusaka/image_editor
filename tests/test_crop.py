"""Tests for crop operations."""

import pytest
from PIL import Image

from image_editor.operations.crop import (
    crop,
    center_crop,
    crop_to_aspect_ratio,
    crop_file,
    PRESET_SIZES,
)


def test_crop_basic(sample_rgb_image):
    result = crop(sample_rgb_image, 10, 10, 50, 50)
    assert result.size == (40, 40)


def test_crop_clamps_to_image_bounds(sample_rgb_image):
    # right/bottom beyond image size should be clamped
    result = crop(sample_rgb_image, 0, 0, 200, 200)
    assert result.size == (100, 100)


def test_crop_negative_left_top(sample_rgb_image):
    # negative coords should be clamped to 0
    result = crop(sample_rgb_image, -10, -10, 50, 50)
    assert result.size == (50, 50)


def test_center_crop_exact(sample_rgb_image):
    result = center_crop(sample_rgb_image, 50, 50)
    assert result.size == (50, 50)


def test_center_crop_larger_than_image(sample_rgb_image):
    # If crop size exceeds image, should be clamped
    result = center_crop(sample_rgb_image, 200, 200)
    assert result.size == (100, 100)


def test_crop_to_aspect_ratio_wider_than_target(sample_rgb_image):
    # 100x100 image (1:1), crop to 16:9 -> result should have 16:9 ratio
    result = crop_to_aspect_ratio(sample_rgb_image, 16, 9)
    w, h = result.size
    assert abs(w / h - 16 / 9) < 0.1


def test_crop_to_aspect_ratio_taller_than_target():
    # 100x200 image (1:2), crop to 1:1 -> result should be 100x100
    img = Image.new("RGB", (100, 200), color=(0, 255, 0))
    result = crop_to_aspect_ratio(img, 1, 1)
    w, h = result.size
    assert abs(w / h - 1.0) < 0.01


def test_crop_file(tmp_path, tmp_image_file):
    output = str(tmp_path / "cropped.png")
    crop_file(tmp_image_file, output, 0, 0, 50, 50)
    with Image.open(output) as img:
        assert img.size == (50, 50)


def test_preset_sizes_defined():
    assert "passport" in PRESET_SIZES
    assert "id_photo" in PRESET_SIZES
    assert "instagram_square" in PRESET_SIZES
