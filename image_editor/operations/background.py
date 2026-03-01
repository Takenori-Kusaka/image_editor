"""Background operations: removal, transparency, and replacement."""

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


def background_file(
    input_path: str,
    output_path: str,
    action: str = "remove",
    threshold: int = 30,
    color: tuple = (255, 255, 255),
) -> str:
    """Process background of an image file.

    Args:
        input_path: Path to input image.
        output_path: Path to save output image.
        action: One of 'remove' (make transparent) or 'replace' (replace with color).
        threshold: Color distance threshold.
        color: New background color for 'replace' action.

    Returns:
        Path to the output file.
    """
    with Image.open(input_path) as img:
        if action == "remove":
            result = make_transparent(img, threshold=threshold)
        elif action == "replace":
            result = replace_background(img, new_background=color, threshold=threshold)
        else:
            raise ValueError(f"Unknown action '{action}'. Use 'remove' or 'replace'.")
        result.save(output_path)
    return output_path
