"""Image resizing operations."""

from PIL import Image

from image_editor.operations.crop import PRESET_SIZES


def resize(
    image: Image.Image,
    width: int,
    height: int,
    keep_aspect: bool = False,
    resample: int = Image.LANCZOS,
) -> Image.Image:
    """Resize an image to specified dimensions.

    Args:
        image: Input PIL Image.
        width: Target width. Use 0 to calculate from height while keeping aspect ratio.
        height: Target height. Use 0 to calculate from width while keeping aspect ratio.
        keep_aspect: If True, resize to fit within width x height while preserving aspect ratio.
        resample: Resampling filter (default LANCZOS).

    Returns:
        Resized PIL Image.
    """
    if width <= 0 and height <= 0:
        raise ValueError("At least one of width or height must be positive.")

    img_width, img_height = image.size

    if width <= 0:
        # Calculate width to maintain aspect ratio
        ratio = height / img_height
        width = max(1, int(img_width * ratio))
    elif height <= 0:
        # Calculate height to maintain aspect ratio
        ratio = width / img_width
        height = max(1, int(img_height * ratio))
    elif keep_aspect:
        # Fit within width x height while preserving aspect ratio
        ratio = min(width / img_width, height / img_height)
        width = max(1, int(img_width * ratio))
        height = max(1, int(img_height * ratio))

    return image.resize((width, height), resample=resample)


def resize_to_preset(
    image: Image.Image,
    preset: str,
    keep_aspect: bool = False,
    fill_color: tuple = (255, 255, 255),
) -> Image.Image:
    """Resize an image to a preset size.

    Args:
        image: Input PIL Image.
        preset: Preset name (e.g., 'passport', 'id_photo', 'instagram_square').
        keep_aspect: If True, fit within preset dimensions while preserving aspect ratio
                     and pad with fill_color.
        fill_color: Background fill color when keep_aspect is True.

    Returns:
        Resized PIL Image.
    """
    if preset not in PRESET_SIZES:
        available = ", ".join(PRESET_SIZES.keys())
        raise ValueError(f"Unknown preset '{preset}'. Available presets: {available}")

    target_width, target_height = PRESET_SIZES[preset]

    if keep_aspect:
        resized = resize(image, target_width, target_height, keep_aspect=True)
        # Pad to exact preset size
        result = Image.new(
            "RGBA" if image.mode == "RGBA" else "RGB",
            (target_width, target_height),
            fill_color,
        )
        offset_x = (target_width - resized.size[0]) // 2
        offset_y = (target_height - resized.size[1]) // 2
        result.paste(resized, (offset_x, offset_y))
        return result
    else:
        return resize(image, target_width, target_height)


def resize_file(
    input_path: str,
    output_path: str,
    width: int,
    height: int,
    keep_aspect: bool = False,
    preset: str = None,
) -> str:
    """Resize an image file.

    Args:
        input_path: Path to input image.
        output_path: Path to save resized image.
        width: Target width.
        height: Target height.
        keep_aspect: Preserve aspect ratio.
        preset: Preset name (overrides width/height if specified).

    Returns:
        Path to the output file.
    """
    with Image.open(input_path) as img:
        if preset:
            result = resize_to_preset(img, preset, keep_aspect=keep_aspect)
        else:
            result = resize(img, width, height, keep_aspect=keep_aspect)
        result.save(output_path)
    return output_path
