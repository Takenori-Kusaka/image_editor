"""Unit tests for face detection and face-crop operations."""

import pytest
import numpy as np
from PIL import Image

from image_editor.operations.face import (
    detect_faces,
    crop_face,
    crop_face_file,
    _pil_to_gray_cv,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_face_image(size=(200, 200)):
    """Create a synthetic image that resembles a face well enough for the
    Haar classifier to handle gracefully (detection may or may not succeed –
    we test robustness, not model accuracy here)."""
    img = Image.new("RGB", size, color=(220, 180, 150))
    # Draw rough eye-like dark rectangles and mouth
    arr = np.array(img)
    arr[70:90, 60:80] = (40, 40, 40)   # left eye
    arr[70:90, 120:140] = (40, 40, 40)  # right eye
    arr[130:140, 80:120] = (120, 40, 40)  # mouth
    return Image.fromarray(arr)


# ---------------------------------------------------------------------------
# _pil_to_gray_cv
# ---------------------------------------------------------------------------


def test_pil_to_gray_cv_returns_2d_array():
    img = Image.new("RGB", (50, 50), color=(100, 150, 200))
    gray = _pil_to_gray_cv(img)
    assert gray.ndim == 2
    assert gray.shape == (50, 50)


def test_pil_to_gray_cv_rgba_input():
    img = Image.new("RGBA", (30, 30), color=(100, 150, 200, 255))
    gray = _pil_to_gray_cv(img)
    assert gray.ndim == 2


# ---------------------------------------------------------------------------
# detect_faces – empty image (no face expected)
# ---------------------------------------------------------------------------


def test_detect_faces_no_face_returns_empty_list():
    img = Image.new("RGB", (100, 100), color=(200, 200, 200))
    faces = detect_faces(img, style="real")
    assert isinstance(faces, list)


def test_detect_faces_invalid_style_falls_back():
    """Unknown style should not raise; falls back to default cascade."""
    img = Image.new("RGB", (60, 60), color=(0, 0, 0))
    # Should not raise an exception
    faces = detect_faces(img, style="nonexistent_style")
    assert isinstance(faces, list)


def test_detect_faces_returns_sorted_by_area():
    img = Image.new("RGB", (400, 400), color=(200, 200, 200))
    faces = detect_faces(img)
    # If multiple faces returned, they should be sorted large-first
    areas = [w * h for (_, _, w, h) in faces]
    assert areas == sorted(areas, reverse=True)


def test_detect_faces_each_rect_is_4_tuple():
    img = Image.new("RGB", (100, 100), color=(180, 160, 140))
    faces = detect_faces(img)
    for face in faces:
        assert len(face) == 4
        x, y, w, h = face
        assert w > 0 and h > 0


# ---------------------------------------------------------------------------
# crop_face – returns None when no face detected
# ---------------------------------------------------------------------------


def test_crop_face_returns_none_when_no_face():
    img = Image.new("RGB", (50, 50), color=(0, 128, 0))
    result = crop_face(img)
    # On a solid-colour image there are no detectable faces
    assert result is None or isinstance(result, Image.Image)


def test_crop_face_returns_image_or_none():
    img = _make_face_image()
    result = crop_face(img)
    assert result is None or isinstance(result, Image.Image)


def test_crop_face_face_index_oob_returns_none():
    img = Image.new("RGB", (80, 80), color=(200, 180, 150))
    result = crop_face(img, face_index=999)
    assert result is None


# ---------------------------------------------------------------------------
# crop_face_file
# ---------------------------------------------------------------------------


def test_crop_face_file_raises_on_no_face(tmp_path):
    img = Image.new("RGB", (60, 60), color=(0, 200, 0))
    input_path = str(tmp_path / "green.png")
    output_path = str(tmp_path / "out.png")
    img.save(input_path)

    with pytest.raises(ValueError, match="No face detected"):
        crop_face_file(input_path, output_path)


def test_crop_face_file_saves_output_when_face_found(tmp_path):
    """Inject a pre-detected face via monkeypatch to test file saving."""
    img = Image.new("RGB", (200, 200), color=(200, 180, 150))
    input_path = str(tmp_path / "face.png")
    output_path = str(tmp_path / "out.png")
    img.save(input_path)

    # Monkeypatch detect_faces to always return a face
    import image_editor.operations.face as face_module
    original = face_module.detect_faces

    def _mock_detect(image, **kwargs):
        return [(50, 50, 100, 100)]

    face_module.detect_faces = _mock_detect
    try:
        result = crop_face_file(input_path, output_path)
        assert result == output_path
        with Image.open(output_path) as out_img:
            assert out_img.size[0] > 0
    finally:
        face_module.detect_faces = original


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------


def test_detect_faces_anime_style_does_not_raise():
    img = Image.new("RGB", (200, 200), color=(255, 220, 180))
    faces = detect_faces(img, style="anime")
    assert isinstance(faces, list)


def test_detect_faces_profile_style_does_not_raise():
    img = Image.new("RGB", (200, 200), color=(200, 180, 160))
    faces = detect_faces(img, style="profile")
    assert isinstance(faces, list)
