"""Shared test fixtures and helpers."""

import pytest
import numpy as np
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
def person_silhouette_image():
    """Create a 200x300 image with a person-like silhouette on a blue background.

    This is a synthetic test image with a clearly distinct foreground (skin tone
    coloured oval head + rectangular body) on a solid blue background.  It is
    suitable for testing any background-removal method including rembg.
    """
    width, height = 200, 300
    # Blue background
    arr = np.full((height, width, 3), fill_value=[60, 120, 200], dtype=np.uint8)

    # Head – skin-toned ellipse at top-centre
    cy_head, cx_head = 70, 100
    ry, rx = 35, 28
    for y in range(height):
        for x in range(width):
            if ((y - cy_head) / ry) ** 2 + ((x - cx_head) / rx) ** 2 <= 1.0:
                arr[y, x] = [200, 160, 130]  # skin tone

    # Body – rectangular torso + shoulders
    arr[105:250, 55:145] = [80, 80, 120]   # dark clothing
    arr[105:140, 40:160] = [80, 80, 120]   # shoulders

    return Image.fromarray(arr)


@pytest.fixture
def person_silhouette_file(tmp_path, person_silhouette_image):
    """Save the person silhouette image to a temp file and return the path."""
    path = tmp_path / "person.png"
    person_silhouette_image.save(str(path))
    return str(path)


@pytest.fixture
def tmp_image_file(tmp_path, sample_rgb_image):
    """Save a sample image to a temp file and return the path."""
    path = tmp_path / "sample.png"
    sample_rgb_image.save(str(path))
    return str(path)
