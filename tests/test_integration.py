"""Integration tests – combine multiple operations in a pipeline."""

import json
import pytest
from pathlib import Path
from PIL import Image

from image_editor.operations import (
    resize,
    crop,
    convert_file,
    background_file,
    resize_file,
    crop_file,
    remove_background_grabcut,
    _image_to_svg,
)
from image_editor.settings import Settings


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def rgb_100x100(tmp_path):
    img = Image.new("RGB", (100, 100), color=(200, 100, 50))
    p = tmp_path / "source.png"
    img.save(str(p))
    return str(p)


@pytest.fixture
def white_bg_image(tmp_path):
    img = Image.new("RGB", (80, 80), color=(255, 255, 255))
    for x in range(30, 50):
        for y in range(30, 50):
            img.putpixel((x, y), (255, 0, 0))
    p = tmp_path / "white_bg.png"
    img.save(str(p))
    return str(p)


# ---------------------------------------------------------------------------
# Resize → Convert pipeline
# ---------------------------------------------------------------------------


def test_resize_then_convert_to_webp(tmp_path, rgb_100x100):
    """Resize a PNG to 50x50, then convert it to WebP."""
    resized = str(tmp_path / "resized.png")
    webp = str(tmp_path / "out.webp")

    resize_file(rgb_100x100, resized, 50, 50)
    convert_file(resized, webp)

    with Image.open(webp) as img:
        assert img.format == "WEBP"
        assert img.size == (50, 50)


def test_resize_then_convert_to_svg(tmp_path, rgb_100x100):
    """Resize a PNG then export it as an embedded SVG."""
    resized = str(tmp_path / "resized.png")
    svg_out = str(tmp_path / "out.svg")

    resize_file(rgb_100x100, resized, 40, 40)
    convert_file(resized, svg_out, target_format="SVG")

    content = Path(svg_out).read_text(encoding="utf-8")
    assert "<svg" in content
    assert 'width="40"' in content
    assert "data:image" in content


# ---------------------------------------------------------------------------
# Crop → Resize → Convert pipeline
# ---------------------------------------------------------------------------


def test_crop_resize_convert_pipeline(tmp_path, rgb_100x100):
    """Crop to 60x60, resize to 30x30, convert to JPEG."""
    cropped = str(tmp_path / "cropped.png")
    resized = str(tmp_path / "resized.png")
    jpeg = str(tmp_path / "final.jpg")

    crop_file(rgb_100x100, cropped, 20, 20, 80, 80)
    resize_file(cropped, resized, 30, 30)
    convert_file(resized, jpeg, target_format="JPEG")

    with Image.open(jpeg) as img:
        assert img.format == "JPEG"
        assert img.size == (30, 30)


# ---------------------------------------------------------------------------
# Background removal then format conversion
# ---------------------------------------------------------------------------


def test_remove_bg_then_convert_to_png(tmp_path, white_bg_image):
    """Remove white background (flood), ensure RGBA output is saved as PNG."""
    transparent = str(tmp_path / "transparent.png")
    png_out = str(tmp_path / "final.png")

    background_file(white_bg_image, transparent, action="remove", threshold=30)
    convert_file(transparent, png_out, target_format="PNG")

    with Image.open(png_out) as img:
        assert img.mode == "RGBA"


# ---------------------------------------------------------------------------
# GrabCut background removal
# ---------------------------------------------------------------------------


def test_grabcut_bg_removal_produces_rgba(tmp_path, rgb_100x100):
    """GrabCut should produce an RGBA image (smoke test)."""
    out = str(tmp_path / "grabcut.png")
    background_file(rgb_100x100, out, action="remove", method="grabcut", grabcut_iterations=2)
    with Image.open(out) as img:
        assert img.mode == "RGBA"


# ---------------------------------------------------------------------------
# rembg background removal
# ---------------------------------------------------------------------------


def test_rembg_bg_removal_produces_rgba(tmp_path):
    """rembg should produce an RGBA image with transparent background."""
    import numpy as np
    arr = np.full((100, 100, 3), fill_value=[60, 120, 200], dtype=np.uint8)
    arr[25:75, 30:70] = [200, 160, 130]
    img = Image.fromarray(arr)
    input_path = str(tmp_path / "person.png")
    img.save(input_path)

    out = str(tmp_path / "rembg.png")
    background_file(input_path, out, action="remove", method="rembg")
    with Image.open(out) as result:
        assert result.mode == "RGBA"


def test_rembg_bg_replace_pipeline(tmp_path):
    """rembg replace → resize pipeline produces correct dimensions."""
    import numpy as np
    arr = np.full((200, 150, 3), fill_value=[80, 160, 80], dtype=np.uint8)
    arr[40:160, 30:120] = [200, 160, 130]
    img = Image.fromarray(arr)
    input_path = str(tmp_path / "person.png")
    img.save(input_path)

    bg_out = str(tmp_path / "white_bg.png")
    background_file(input_path, bg_out, action="replace", method="rembg", color=(255, 255, 255))

    resized_out = str(tmp_path / "final.jpg")
    resize_file(bg_out, resized_out, 100, 100)
    with Image.open(resized_out) as result:
        assert result.size == (100, 100)


# ---------------------------------------------------------------------------
# Settings-driven pipeline
# ---------------------------------------------------------------------------


def test_settings_drive_quality(tmp_path, rgb_100x100):
    """Settings file overrides JPEG quality used in conversion."""
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps({"jpeg_quality": 50}), encoding="utf-8")

    s = Settings.load(settings_file)
    quality = s.get("jpeg_quality")

    out = str(tmp_path / "out.jpg")
    convert_file(rgb_100x100, out, target_format="JPEG", quality=quality)

    with Image.open(out) as img:
        assert img.format == "JPEG"


def test_settings_persist_and_reload(tmp_path):
    """Verify round-trip: save settings, reload, values match."""
    p = tmp_path / "settings.json"
    s = Settings.from_dict({"jpeg_quality": 77, "bg_method": "grabcut"})
    s.save(p)

    s2 = Settings.load(p)
    assert s2.get("jpeg_quality") == 77
    assert s2.get("bg_method") == "grabcut"


# ---------------------------------------------------------------------------
# SVG helper unit test
# ---------------------------------------------------------------------------


def test_image_to_svg_contains_expected_elements():
    img = Image.new("RGB", (64, 32), color=(0, 0, 255))
    svg = _image_to_svg(img)
    assert "<svg" in svg
    assert 'width="64"' in svg
    assert 'height="32"' in svg
    assert "data:image/jpeg;base64," in svg


def test_image_to_svg_rgba_uses_png_embed():
    img = Image.new("RGBA", (32, 32), color=(0, 200, 0, 128))
    svg = _image_to_svg(img)
    assert "data:image/png;base64," in svg
