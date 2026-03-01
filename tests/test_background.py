"""Tests for background operations."""

import pytest
from PIL import Image

from image_editor.operations.background import (
    remove_background_color,
    replace_background,
    make_transparent,
    background_file,
    _color_distance,
)


def test_color_distance_same():
    assert _color_distance((255, 0, 0), (255, 0, 0)) == 0.0


def test_color_distance_opposite():
    d = _color_distance((0, 0, 0), (255, 255, 255))
    assert d > 400  # sqrt(3 * 255^2) ~= 441


def test_make_transparent_white_bg(sample_white_bg_image):
    result = make_transparent(sample_white_bg_image, threshold=30)
    assert result.mode == "RGBA"
    # Top-left corner (white bg) should be transparent
    r, g, b, a = result.getpixel((0, 0))
    assert a == 0


def test_make_transparent_preserves_foreground(sample_white_bg_image):
    result = make_transparent(sample_white_bg_image, threshold=30)
    # Center pixel (red) should remain opaque
    r, g, b, a = result.getpixel((50, 50))
    assert a > 0
    assert r > 200  # red channel visible


def test_replace_background(sample_white_bg_image):
    result = replace_background(sample_white_bg_image, new_background=(0, 0, 255))
    assert result.mode == "RGB"
    # Corner should now be blue
    r, g, b = result.getpixel((0, 0))
    assert b > 200
    assert r < 50


def test_remove_background_color_returns_rgba(sample_rgb_image):
    result = remove_background_color(sample_rgb_image, threshold=10)
    assert result.mode == "RGBA"


def test_background_file_remove(tmp_path, tmp_path_factory):
    # Create a white-bg image
    img = Image.new("RGB", (60, 60), color=(255, 255, 255))
    for x in range(20, 40):
        for y in range(20, 40):
            img.putpixel((x, y), (0, 200, 0))
    input_path = str(tmp_path / "input.png")
    output_path = str(tmp_path / "output.png")
    img.save(input_path)

    background_file(input_path, output_path, action="remove", threshold=30)

    with Image.open(output_path) as out:
        assert out.mode == "RGBA"
        r, g, b, a = out.getpixel((0, 0))
        assert a == 0  # background transparent


def test_background_file_replace(tmp_path):
    img = Image.new("RGB", (60, 60), color=(255, 255, 255))
    for x in range(20, 40):
        for y in range(20, 40):
            img.putpixel((x, y), (0, 200, 0))
    input_path = str(tmp_path / "input.png")
    output_path = str(tmp_path / "output.png")
    img.save(input_path)

    background_file(input_path, output_path, action="replace", threshold=30, color=(0, 0, 255))

    with Image.open(output_path) as out:
        r, g, b = out.getpixel((0, 0))
        assert b > 200  # replaced with blue


def test_background_file_invalid_action(tmp_path, tmp_image_file):
    output = str(tmp_path / "out.png")
    with pytest.raises(ValueError, match="Unknown action"):
        background_file(tmp_image_file, output, action="invalid")


# ---------------------------------------------------------------------------
# GrabCut method
# ---------------------------------------------------------------------------


def test_grabcut_remove_returns_rgba(sample_rgb_image):
    from image_editor.operations.background import remove_background_grabcut
    result = remove_background_grabcut(sample_rgb_image, iterations=2)
    assert result.mode == "RGBA"
    assert result.size == sample_rgb_image.size


def test_grabcut_replace_returns_rgb(sample_rgb_image):
    from image_editor.operations.background import replace_background_grabcut
    result = replace_background_grabcut(sample_rgb_image, new_background=(0, 0, 255), iterations=2)
    assert result.mode == "RGB"
    assert result.size == sample_rgb_image.size


def test_background_file_grabcut_remove(tmp_path, tmp_image_file):
    output = str(tmp_path / "grabcut_out.png")
    background_file(tmp_image_file, output, action="remove", method="grabcut", grabcut_iterations=2)
    with Image.open(output) as img:
        assert img.mode == "RGBA"


def test_background_file_grabcut_replace(tmp_path, tmp_image_file):
    output = str(tmp_path / "grabcut_replace.png")
    background_file(
        tmp_image_file, output,
        action="replace", method="grabcut", color=(0, 0, 200), grabcut_iterations=2,
    )
    with Image.open(output) as img:
        assert img.mode == "RGB"


def test_background_file_grabcut_invalid_action(tmp_path, tmp_image_file):
    output = str(tmp_path / "out.png")
    with pytest.raises(ValueError, match="Unknown action"):
        background_file(tmp_image_file, output, action="invalid", method="grabcut")


# ---------------------------------------------------------------------------
# rembg (U²-Net deep-learning) method
# ---------------------------------------------------------------------------


def test_rembg_remove_returns_rgba(person_silhouette_image):
    from image_editor.operations.background import remove_background_rembg
    result = remove_background_rembg(person_silhouette_image, model_name="u2net")
    assert result.mode == "RGBA"
    assert result.size == person_silhouette_image.size


def test_rembg_replace_returns_rgb(person_silhouette_image):
    from image_editor.operations.background import replace_background_rembg
    result = replace_background_rembg(
        person_silhouette_image, new_background=(255, 255, 255), model_name="u2net",
    )
    assert result.mode == "RGB"
    assert result.size == person_silhouette_image.size


def test_rembg_replaces_background_color(person_silhouette_image):
    """Verify that the blue background is actually replaced with white."""
    from image_editor.operations.background import replace_background_rembg
    result = replace_background_rembg(
        person_silhouette_image, new_background=(255, 255, 255), model_name="u2net",
    )
    # The corner pixel (pure background) should be close to white now
    r, g, b = result.getpixel((0, 0))
    assert r > 200 and g > 200 and b > 200, f"Corner pixel should be white, got ({r},{g},{b})"


def test_background_file_rembg_remove(tmp_path, person_silhouette_file):
    output = str(tmp_path / "rembg_out.png")
    background_file(person_silhouette_file, output, action="remove", method="rembg")
    with Image.open(output) as img:
        assert img.mode == "RGBA"


def test_background_file_rembg_replace(tmp_path, person_silhouette_file):
    output = str(tmp_path / "rembg_replace.png")
    background_file(
        person_silhouette_file, output,
        action="replace", method="rembg", color=(0, 255, 0),
    )
    with Image.open(output) as img:
        assert img.mode == "RGB"


def test_background_file_rembg_invalid_action(tmp_path, person_silhouette_file):
    output = str(tmp_path / "out.png")
    with pytest.raises(ValueError, match="Unknown action"):
        background_file(person_silhouette_file, output, action="invalid", method="rembg")

