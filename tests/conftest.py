"""Shared test fixtures and helpers."""

import pytest
from PIL import Image


@pytest.fixture
def sample_rgb_image():
    """Create a simple 100x100 red RGB image."""
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    return img


@pytest.fixture
def sample_rgba_image():
    """Create a simple 100x100 RGBA image."""
    img = Image.new("RGBA", (100, 100), color=(0, 128, 255, 255))
    return img


@pytest.fixture
def sample_white_bg_image():
    """Create a 100x100 image with white background and a red square in the center."""
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    for x in range(40, 60):
        for y in range(40, 60):
            img.putpixel((x, y), (255, 0, 0))
    return img


@pytest.fixture
def tmp_image_file(tmp_path, sample_rgb_image):
    """Save a sample image to a temp file and return the path."""
    path = tmp_path / "sample.png"
    sample_rgb_image.save(str(path))
    return str(path)
