"""Image format conversion operations."""

from pathlib import Path
from PIL import Image


# Mapping of common format aliases to Pillow format strings
FORMAT_ALIASES = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
    "gif": "GIF",
    "bmp": "BMP",
    "tiff": "TIFF",
    "tif": "TIFF",
    "ico": "ICO",
}

# Formats that support transparency (alpha channel)
TRANSPARENCY_FORMATS = {"PNG", "WEBP", "GIF", "ICO"}

# Default JPEG quality
DEFAULT_JPEG_QUALITY = 95


def normalize_format(fmt: str) -> str:
    """Normalize a format string to Pillow format name.

    Args:
        fmt: Format string (e.g., 'jpg', 'JPEG', 'png').

    Returns:
        Normalized Pillow format string (e.g., 'JPEG', 'PNG').
    """
    normalized = FORMAT_ALIASES.get(fmt.lower(), fmt.upper())
    return normalized


def convert(
    image: Image.Image,
    target_format: str,
    quality: int = DEFAULT_JPEG_QUALITY,
    background_color: tuple = (255, 255, 255),
) -> Image.Image:
    """Convert an image to a target format (returns Image in the appropriate mode).

    Args:
        image: Input PIL Image.
        target_format: Target format string (e.g., 'JPEG', 'PNG').
        quality: JPEG quality (1-95).
        background_color: Background color when converting from RGBA to RGB.

    Returns:
        Converted PIL Image.
    """
    fmt = normalize_format(target_format)

    if fmt == "JPEG" and image.mode in ("RGBA", "LA", "P"):
        # JPEG doesn't support transparency; composite onto background
        bg = Image.new("RGB", image.size, background_color)
        if image.mode == "P":
            image = image.convert("RGBA")
        if image.mode in ("RGBA", "LA"):
            bg.paste(image, mask=image.split()[-1])
        else:
            bg.paste(image)
        return bg
    elif fmt in TRANSPARENCY_FORMATS and image.mode not in ("RGBA", "RGB", "L", "P"):
        return image.convert("RGBA")
    elif fmt == "JPEG" and image.mode != "RGB":
        return image.convert("RGB")
    return image


def convert_file(
    input_path: str,
    output_path: str,
    target_format: str = None,
    quality: int = DEFAULT_JPEG_QUALITY,
    background_color: tuple = (255, 255, 255),
) -> str:
    """Convert an image file to a different format.

    Args:
        input_path: Path to input image.
        output_path: Path to save converted image.
        target_format: Target format (inferred from output_path extension if None).
        quality: JPEG/WebP quality (1-95).
        background_color: Background color for transparency removal.

    Returns:
        Path to the output file.
    """
    if target_format is None:
        suffix = Path(output_path).suffix.lstrip(".")
        target_format = normalize_format(suffix)

    with Image.open(input_path) as img:
        result = convert(img, target_format, quality=quality, background_color=background_color)
        save_kwargs = {}
        fmt = normalize_format(target_format)
        if fmt == "JPEG":
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True
        elif fmt == "WEBP":
            save_kwargs["quality"] = quality
        result.save(output_path, format=fmt, **save_kwargs)
    return output_path
