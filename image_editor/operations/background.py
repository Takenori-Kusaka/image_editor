"""Background operations: removal, transparency, and replacement.

Three removal methods are provided:

* ``"flood"`` – Fast flood-fill from image corners.  Works well for images
  with a uniform solid-colour background (any art style).
* ``"grabcut"`` – OpenCV GrabCut graph-cut segmentation using an auto-detected
  foreground hint.  Handles complex backgrounds and works across real photos,
  3-D renders, and 2-D/anime illustrations.
* ``"rembg"`` – Deep-learning-based segmentation using U²-Net via the *rembg*
  library.  Provides the highest accuracy for person/object segmentation,
  including fine details like hair edges and semi-transparent regions.
  Requires ``pip install rembg[cpu]`` (or ``rembg[gpu]`` for CUDA).
"""

from __future__ import annotations

import numpy as np
import cv2
from PIL import Image, ImageFilter


def _get_alpha_mask(image: Image.Image) -> Image.Image:
    """Extract or create an alpha mask from an image.

    Args:
        image: Input PIL Image.

    Returns:
        Alpha mask as a grayscale Image.
    """
    if image.mode == "RGBA":
        return image.split()[3]
    return Image.new("L", image.size, 255)


def remove_background_color(
    image: Image.Image,
    threshold: int = 30,
    corner_sample: bool = True,
    target_color: tuple = None,
) -> Image.Image:
    """Remove a background color from an image, making it transparent.

    Uses flood-fill from corners to identify and remove the background.

    Args:
        image: Input PIL Image.
        threshold: Color distance threshold (0-255). Higher = more aggressive removal.
        corner_sample: If True, sample background color from image corners.
        target_color: Explicit background color to remove (RGB tuple). Used if corner_sample=False.

    Returns:
        PIL Image with RGBA mode and transparent background.
    """
    rgba = image.convert("RGBA")
    data = rgba.load()
    width, height = rgba.size

    if corner_sample:
        # Sample corners to determine background color
        corners = [
            data[0, 0][:3],
            data[width - 1, 0][:3],
            data[0, height - 1][:3],
            data[width - 1, height - 1][:3],
        ]
        # Use the most common corner color
        bg_color = min(corners, key=lambda c: sum(
            _color_distance(c, other) for other in corners
        ))
    elif target_color is not None:
        bg_color = target_color[:3]
    else:
        bg_color = (255, 255, 255)

    # Flood fill from corners to mark background pixels
    visited = [[False] * height for _ in range(width)]
    queue = []

    # Seed from all four corners
    for sx, sy in [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]:
        if not visited[sx][sy] and _color_distance(data[sx, sy][:3], bg_color) <= threshold:
            queue.append((sx, sy))
            visited[sx][sy] = True

    while queue:
        x, y = queue.pop()
        # Make transparent
        data[x, y] = (data[x, y][0], data[x, y][1], data[x, y][2], 0)
        for nx, ny in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
            if (
                0 <= nx < width
                and 0 <= ny < height
                and not visited[nx][ny]
                and _color_distance(data[nx, ny][:3], bg_color) <= threshold
            ):
                visited[nx][ny] = True
                queue.append((nx, ny))

    return rgba


def replace_background(
    image: Image.Image,
    new_background: tuple = (255, 255, 255),
    threshold: int = 30,
) -> Image.Image:
    """Replace the background of an image with a new color.

    Args:
        image: Input PIL Image (RGBA or RGB).
        new_background: New background color as RGB tuple.
        threshold: Color distance threshold for background detection.

    Returns:
        PIL Image with replaced background (RGB mode).
    """
    if image.mode != "RGBA":
        image = remove_background_color(image, threshold=threshold)

    background = Image.new("RGB", image.size, new_background)
    background.paste(image, mask=image.split()[3])
    return background


def make_transparent(
    image: Image.Image,
    threshold: int = 30,
    target_color: tuple = None,
) -> Image.Image:
    """Make the background of an image transparent.

    Args:
        image: Input PIL Image.
        threshold: Color distance threshold.
        target_color: Specific color to make transparent (optional).

    Returns:
        PIL Image in RGBA mode with transparent background.
    """
    return remove_background_color(image, threshold=threshold, target_color=target_color)


def _color_distance(c1: tuple, c2: tuple) -> float:
    """Calculate Euclidean distance between two RGB colors.

    Args:
        c1: First RGB color tuple.
        c2: Second RGB color tuple.

    Returns:
        Euclidean color distance.
    """
    return ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2) ** 0.5


def remove_background_grabcut(
    image: Image.Image,
    iterations: int = 5,
    border_fraction: float = 0.05,
) -> Image.Image:
    """Remove the background using OpenCV's GrabCut algorithm.

    GrabCut performs graph-cut segmentation that separates a subject from its
    background based on colour and texture cues.  Unlike the flood-fill method
    it handles complex backgrounds and works on real photos, 3-D renders, and
    2-D/anime illustrations.

    The foreground rectangle is inferred automatically as the central 90 % of
    the image.

    Args:
        image: Input PIL Image.
        iterations: Number of GrabCut iterations.  More iterations improve
                    quality at the cost of processing time.
        border_fraction: Fraction of each edge treated as definite background
                         when constructing the initial foreground rectangle.

    Returns:
        PIL Image in RGBA mode with the detected background made transparent.
    """
    rgb = image.convert("RGB")
    arr = np.array(rgb, dtype=np.uint8)

    h, w = arr.shape[:2]
    bx = max(1, int(w * border_fraction))
    by = max(1, int(h * border_fraction))
    # (x, y, width, height) of the foreground hint rectangle
    rect = (bx, by, w - 2 * bx, h - 2 * by)

    mask = np.zeros((h, w), dtype=np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    cv2.grabCut(arr, mask, rect, bgd_model, fgd_model, iterations, cv2.GC_INIT_WITH_RECT)

    # Pixels marked as definite or probable foreground → keep
    foreground_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)

    rgba = image.convert("RGBA")
    alpha_arr = np.array(rgba)
    alpha_arr[:, :, 3] = foreground_mask
    return Image.fromarray(alpha_arr, "RGBA")


def replace_background_grabcut(
    image: Image.Image,
    new_background: tuple = (255, 255, 255),
    iterations: int = 5,
) -> Image.Image:
    """Replace background using GrabCut segmentation.

    Args:
        image: Input PIL Image.
        new_background: Replacement background colour (RGB tuple).
        iterations: GrabCut iterations.

    Returns:
        PIL Image (RGB mode) with the background replaced.
    """
    rgba = remove_background_grabcut(image, iterations=iterations)
    bg = Image.new("RGB", image.size, new_background)
    bg.paste(rgba, mask=rgba.split()[3])
    return bg


# ---------------------------------------------------------------------------
# rembg (U²-Net deep-learning) method
# ---------------------------------------------------------------------------


def _check_rembg_available() -> None:
    """Raise ImportError with a helpful message if rembg is not installed."""
    try:
        import rembg  # noqa: F401
    except ImportError:
        raise ImportError(
            "The 'rembg' package is required for method='rembg'. "
            "Install it with: pip install rembg[cpu]  (or rembg[gpu] for CUDA)"
        )


def remove_background_rembg(
    image: Image.Image,
    model_name: str = "u2net",
    alpha_matting: bool = False,
    alpha_matting_foreground_threshold: int = 240,
    alpha_matting_background_threshold: int = 10,
    alpha_matting_erode_size: int = 10,
) -> Image.Image:
    """Remove background using deep-learning segmentation (U²-Net via rembg).

    This produces significantly higher quality results than GrabCut or flood-fill,
    especially for:
    - Hair edges and fine detail
    - Semi-transparent regions
    - Complex/cluttered backgrounds
    - Person segmentation (clothing, accessories)

    Args:
        image: Input PIL Image.
        model_name: rembg model to use.  ``"u2net"`` (default, general purpose),
                    ``"u2net_human_seg"`` (optimised for human portraits),
                    ``"isnet-general-use"`` (ISNet, high quality).
        alpha_matting: If True, apply alpha matting for finer edge detail
                       (slower but better hair/fur edges).
        alpha_matting_foreground_threshold: Foreground confidence threshold (0-255).
        alpha_matting_background_threshold: Background confidence threshold (0-255).
        alpha_matting_erode_size: Erosion kernel size for matting mask refinement.

    Returns:
        PIL Image in RGBA mode with the detected background made transparent.
    """
    _check_rembg_available()
    from rembg import remove, new_session

    session = new_session(model_name)

    result = remove(
        image,
        session=session,
        alpha_matting=alpha_matting,
        alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
        alpha_matting_background_threshold=alpha_matting_background_threshold,
        alpha_matting_erode_size=alpha_matting_erode_size,
    )

    if result.mode != "RGBA":
        result = result.convert("RGBA")
    return result


def replace_background_rembg(
    image: Image.Image,
    new_background: tuple = (255, 255, 255),
    model_name: str = "u2net",
    alpha_matting: bool = False,
    alpha_matting_foreground_threshold: int = 240,
    alpha_matting_background_threshold: int = 10,
    alpha_matting_erode_size: int = 10,
) -> Image.Image:
    """Replace background using deep-learning segmentation (U²-Net via rembg).

    Args:
        image: Input PIL Image.
        new_background: Replacement background colour (RGB tuple).
        model_name: rembg model name.
        alpha_matting: Enable alpha matting for fine edge detail.
        alpha_matting_foreground_threshold: Foreground confidence (0-255).
        alpha_matting_background_threshold: Background confidence (0-255).
        alpha_matting_erode_size: Erosion size for matting refinement.

    Returns:
        PIL Image (RGB mode) with the background replaced.
    """
    rgba = remove_background_rembg(
        image,
        model_name=model_name,
        alpha_matting=alpha_matting,
        alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
        alpha_matting_background_threshold=alpha_matting_background_threshold,
        alpha_matting_erode_size=alpha_matting_erode_size,
    )
    bg = Image.new("RGB", image.size, new_background)
    bg.paste(rgba, mask=rgba.split()[3])
    return bg


def background_file(
    input_path: str,
    output_path: str,
    action: str = "remove",
    threshold: int = 30,
    color: tuple = (255, 255, 255),
    method: str = "flood",
    grabcut_iterations: int = 5,
    rembg_model: str = "u2net",
    alpha_matting: bool = False,
) -> str:
    """Process background of an image file.

    Args:
        input_path: Path to input image.
        output_path: Path to save output image.
        action: One of ``'remove'`` (make transparent) or ``'replace'``
                (replace with *color*).
        threshold: Colour-distance threshold for the ``"flood"`` method.
        color: Replacement background colour for the ``'replace'`` action.
        method: Segmentation method: ``"flood"`` (default, fast),
                ``"grabcut"`` (edge-aware), or ``"rembg"`` (deep-learning,
                highest accuracy for person/object segmentation).
        grabcut_iterations: Number of GrabCut iterations (only used when
                            *method* is ``"grabcut"``).
        rembg_model: rembg model name (only used when *method* is ``"rembg"``).
                     Options: ``"u2net"``, ``"u2net_human_seg"``,
                     ``"isnet-general-use"``.
        alpha_matting: Enable alpha matting for fine edge detail (only used
                       when *method* is ``"rembg"``).

    Returns:
        Path to the output file.
    """
    with Image.open(input_path) as img:
        if method == "rembg":
            if action == "remove":
                result = remove_background_rembg(
                    img, model_name=rembg_model, alpha_matting=alpha_matting,
                )
            elif action == "replace":
                result = replace_background_rembg(
                    img, new_background=color,
                    model_name=rembg_model, alpha_matting=alpha_matting,
                )
            else:
                raise ValueError(f"Unknown action '{action}'. Use 'remove' or 'replace'.")
        elif method == "grabcut":
            if action == "remove":
                result = remove_background_grabcut(img, iterations=grabcut_iterations)
            elif action == "replace":
                result = replace_background_grabcut(
                    img, new_background=color, iterations=grabcut_iterations
                )
            else:
                raise ValueError(f"Unknown action '{action}'. Use 'remove' or 'replace'.")
        else:
            if action == "remove":
                result = make_transparent(img, threshold=threshold)
            elif action == "replace":
                result = replace_background(img, new_background=color, threshold=threshold)
            else:
                raise ValueError(f"Unknown action '{action}'. Use 'remove' or 'replace'.")
        result.save(output_path)
    return output_path
