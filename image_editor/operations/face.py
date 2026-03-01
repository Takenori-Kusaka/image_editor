"""Face detection and face-crop operations.

Uses OpenCV's built-in Haar Cascade classifiers – no separate model download
is required. Works on real photographs, 3D-rendered images, and (to a lesser
extent) 2D/anime illustrations.

For anime / 2D-style faces the frontal-face cascade performs less reliably;
the anime-specific cascade (``haarcascade_frontalcatface.xml``) can be used
instead via the *style* parameter.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image


# ---------------------------------------------------------------------------
# Cascade catalogue
# ---------------------------------------------------------------------------

_CASCADE_DIR = Path(cv2.data.haarcascades)

# Cascade files bundled with OpenCV, keyed by style hint
_CASCADES = {
    "real": _CASCADE_DIR / "haarcascade_frontalface_default.xml",
    "real_alt": _CASCADE_DIR / "haarcascade_frontalface_alt2.xml",
    "anime": _CASCADE_DIR / "haarcascade_frontalcatface_extended.xml",
    "profile": _CASCADE_DIR / "haarcascade_profileface.xml",
}

# Face rectangle type: (x, y, w, h)
FaceRect = Tuple[int, int, int, int]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_faces(
    image: Image.Image,
    style: str = "real",
    min_size: int = 30,
    scale_factor: float = 1.1,
    min_neighbors: int = 4,
) -> List[FaceRect]:
    """Detect faces in a PIL Image and return their bounding rectangles.

    Detection uses OpenCV Haar Cascade classifiers which are included with
    the ``opencv-python-headless`` package; no model download is needed.

    Args:
        image: Input PIL Image (any mode – converted internally to greyscale).
        style: Detection style.  Use ``"real"`` for photographs and 3-D
               renders; use ``"anime"`` for 2-D / cartoon / illustration faces.
               ``"profile"`` detects side-facing real faces.
        min_size: Minimum face size in pixels (width **and** height).
        scale_factor: Scale factor between image pyramid levels.
        min_neighbors: Higher = fewer false positives, lower = more detections.

    Returns:
        List of ``(x, y, w, h)`` tuples for each detected face, sorted by
        decreasing face area (largest face first).
    """
    cascade_path = _CASCADES.get(style, _CASCADES["real"])
    cascade = cv2.CascadeClassifier(str(cascade_path))

    gray = _pil_to_gray_cv(image)

    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=scale_factor,
        minNeighbors=min_neighbors,
        minSize=(min_size, min_size),
    )

    if not isinstance(faces, np.ndarray) or len(faces) == 0:
        return []

    # Sort by area descending (largest / most prominent face first)
    faces_list: List[FaceRect] = [
        (int(x), int(y), int(w), int(h)) for x, y, w, h in faces
    ]
    faces_list.sort(key=lambda r: r[2] * r[3], reverse=True)
    return faces_list


def crop_face(
    image: Image.Image,
    padding: float = 0.2,
    style: str = "real",
    min_size: int = 30,
    face_index: int = 0,
) -> Optional[Image.Image]:
    """Detect and crop the *face_index*-th face (largest by default) from an image.

    Args:
        image: Input PIL Image.
        padding: Fractional padding added around the detected face rectangle.
                 ``0.2`` adds 20 % of the face width/height on each side.
        style: Cascade style (see :func:`detect_faces`).
        min_size: Minimum face size in pixels.
        face_index: Index into the list of detected faces sorted by decreasing
                    area.  ``0`` = largest face.

    Returns:
        Cropped PIL Image around the selected face, or ``None`` if no face is
        detected.
    """
    faces = detect_faces(image, style=style, min_size=min_size)
    if not faces or face_index >= len(faces):
        return None

    x, y, w, h = faces[face_index]
    img_w, img_h = image.size

    pad_x = int(w * padding)
    pad_y = int(h * padding)

    left = max(0, x - pad_x)
    top = max(0, y - pad_y)
    right = min(img_w, x + w + pad_x)
    bottom = min(img_h, y + h + pad_y)

    return image.crop((left, top, right, bottom))


def crop_face_file(
    input_path: str,
    output_path: str,
    padding: float = 0.2,
    style: str = "real",
    min_size: int = 30,
    face_index: int = 0,
) -> str:
    """Detect and crop a face from an image file.

    Args:
        input_path: Path to input image.
        output_path: Path to save the cropped face image.
        padding: Fractional padding (see :func:`crop_face`).
        style: Cascade style (``"real"`` or ``"anime"``).
        min_size: Minimum face size in pixels.
        face_index: Index of the face to crop (0 = largest).

    Returns:
        Path to the output file.

    Raises:
        ValueError: If no face is detected in the image.
    """
    with Image.open(input_path) as img:
        result = crop_face(img, padding=padding, style=style, min_size=min_size, face_index=face_index)
    if result is None:
        raise ValueError(f"No face detected in '{input_path}'.")
    result.save(output_path)
    return output_path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _pil_to_gray_cv(image: Image.Image) -> np.ndarray:
    """Convert a PIL Image to an OpenCV grayscale array."""
    rgb = image.convert("RGB")
    arr = np.array(rgb)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    return gray
