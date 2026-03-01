"""Tests for format conversion operations."""

import pytest
from PIL import Image

from image_editor.operations.convert import (
    convert,
    convert_file,
    normalize_format,
    FORMAT_ALIASES,
)


def test_normalize_format_jpeg():
    assert normalize_format("jpg") == "JPEG"
    assert normalize_format("jpeg") == "JPEG"
    assert normalize_format("JPG") == "JPEG"


def test_normalize_format_png():
    assert normalize_format("png") == "PNG"
    assert normalize_format("PNG") == "PNG"


def test_normalize_format_webp():
    assert normalize_format("webp") == "WEBP"


def test_normalize_format_tiff():
    assert normalize_format("tif") == "TIFF"
    assert normalize_format("tiff") == "TIFF"


def test_convert_rgba_to_jpeg(sample_rgba_image):
    result = convert(sample_rgba_image, "JPEG")
    assert result.mode == "RGB"


def test_convert_rgb_to_png(sample_rgb_image):
    result = convert(sample_rgb_image, "PNG")
    assert result.mode == "RGB"


def test_convert_png_to_jpeg_removes_alpha(sample_rgba_image):
    result = convert(sample_rgba_image, "JPEG")
    assert result.mode == "RGB"
    # Alpha channel should be removed
    assert len(result.split()) == 3


def test_convert_file_png_to_jpeg(tmp_path, tmp_image_file):
    output = str(tmp_path / "out.jpg")
    convert_file(tmp_image_file, output, target_format="JPEG")
    with Image.open(output) as img:
        assert img.format == "JPEG"


def test_convert_file_infers_format_from_extension(tmp_path, tmp_image_file):
    output = str(tmp_path / "out.webp")
    convert_file(tmp_image_file, output)
    with Image.open(output) as img:
        assert img.format == "WEBP"


def test_convert_file_png_to_png(tmp_path, tmp_image_file):
    output = str(tmp_path / "out.png")
    convert_file(tmp_image_file, output, target_format="PNG")
    with Image.open(output) as img:
        assert img.format == "PNG"


def test_format_aliases_contains_common_formats():
    assert "jpg" in FORMAT_ALIASES
    assert "png" in FORMAT_ALIASES
    assert "webp" in FORMAT_ALIASES
    assert "gif" in FORMAT_ALIASES
    assert "bmp" in FORMAT_ALIASES
