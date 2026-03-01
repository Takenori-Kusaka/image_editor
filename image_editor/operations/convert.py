"""Image format conversion operations."""

from __future__ import annotations

import base64
import io
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
    "svg": "SVG",   # handled specially – raster embedded in SVG wrapper
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


def _image_to_svg(image: Image.Image, quality: int = DEFAULT_JPEG_QUALITY) -> str:
    """Embed a raster image inside an SVG wrapper.

    The raster pixels are Base64-encoded as a PNG (or JPEG if the image has no
    alpha channel) and placed inside an ``<image>`` element.  The resulting SVG
    is a valid, viewable SVG file suitable for web use.

    Args:
        image: Input PIL Image.
        quality: JPEG quality used when the image is opaque.

    Returns:
        SVG document as a UTF-8 string.
    """
    w, h = image.size
    buf = io.BytesIO()
    if image.mode == "RGBA":
        image.save(buf, format="PNG")
        mime = "image/png"
    else:
        image.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
        mime = "image/jpeg"
    data_uri = "data:{};base64,{}".format(mime, base64.b64encode(buf.getvalue()).decode())
    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
        f'  <image xlink:href="{data_uri}" width="{w}" height="{h}"/>\n'
        "</svg>\n"
    )
    return svg


def convert_file(
    input_path: str,
    output_path: str,
    target_format: str = None,
    quality: int = DEFAULT_JPEG_QUALITY,
    background_color: tuple = (255, 255, 255),
) -> str:
    """Convert an image file to a different format.

    Supports all PIL-readable formats plus **SVG** output (raster image
    embedded in an SVG wrapper, suitable for web use).

    Args:
        input_path: Path to input image.
        output_path: Path to save converted image.
        target_format: Target format (inferred from output_path extension if None).
                       Use ``"svg"`` or ``"SVG"`` for SVG output.
        quality: JPEG/WebP quality (1-95).
        background_color: Background color for transparency removal.

    Returns:
        Path to the output file.
    """
    if target_format is None:
        suffix = Path(output_path).suffix.lstrip(".")
        target_format = normalize_format(suffix)

    fmt = normalize_format(target_format)

    # SVG is handled separately – it's not a PIL format
    if fmt == "SVG":
        with Image.open(input_path) as img:
            svg_content = _image_to_svg(img, quality=quality)
        Path(output_path).write_text(svg_content, encoding="utf-8")
        return output_path

    with Image.open(input_path) as img:
        result = convert(img, target_format, quality=quality, background_color=background_color)
        save_kwargs = {}
        if fmt == "JPEG":
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True
        elif fmt == "WEBP":
            save_kwargs["quality"] = quality
        result.save(output_path, format=fmt, **save_kwargs)
    return output_path
