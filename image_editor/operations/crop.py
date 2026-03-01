"""Image cropping operations."""

from pathlib import Path
from PIL import Image


# Preset photo sizes (width x height in pixels at common DPI)
PRESET_SIZES = {
    "id_photo": (600, 800),          # 3x4cm @ 200dpi
    "passport": (413, 531),           # 35x45mm @ 300dpi
    "mynumber": (413, 531),           # 35x45mm @ 300dpi (マイナンバーカード)
    "resume": (354, 472),             # 30x40mm @ 300dpi (履歴書)
    "drivers_license": (283, 354),    # 24x30mm @ 300dpi (運転免許証)
    "business_card": (1063, 591),     # 91x55mm @ 300dpi
    "a4": (2480, 3508),               # A4 @ 300dpi
    "a5": (1748, 2480),               # A5 @ 300dpi
    "instagram_square": (1080, 1080), # Instagram square
    "instagram_portrait": (1080, 1350), # Instagram portrait
    "twitter_header": (1500, 500),    # Twitter header
    "facebook_cover": (820, 312),     # Facebook cover
    "fullhd": (1920, 1080),           # Full HD
    "4k": (3840, 2160),              # 4K UHD
}


def crop(image: Image.Image, left: int, top: int, right: int, bottom: int) -> Image.Image:
    """Crop an image to specified coordinates.

    Args:
        image: Input PIL Image.
        left: Left coordinate.
        top: Top coordinate.
        right: Right coordinate.
        bottom: Bottom coordinate.

    Returns:
        Cropped PIL Image.
    """
    width, height = image.size
    left = max(0, left)
    top = max(0, top)
    right = min(width, right)
    bottom = min(height, bottom)
    return image.crop((left, top, right, bottom))


def center_crop(image: Image.Image, width: int, height: int) -> Image.Image:
    """Center crop an image to specified dimensions.

    Args:
        image: Input PIL Image.
        width: Target width.
        height: Target height.

    Returns:
        Center-cropped PIL Image.
    """
    img_width, img_height = image.size
    left = (img_width - width) // 2
    top = (img_height - height) // 2
    right = left + width
    bottom = top + height
    left = max(0, left)
    top = max(0, top)
    right = min(img_width, right)
    bottom = min(img_height, bottom)
    return image.crop((left, top, right, bottom))


def crop_to_aspect_ratio(image: Image.Image, width_ratio: int, height_ratio: int) -> Image.Image:
    """Crop an image to a specific aspect ratio (center crop).

    Args:
        image: Input PIL Image.
        width_ratio: Width part of the aspect ratio.
        height_ratio: Height part of the aspect ratio.

    Returns:
        Cropped PIL Image with the specified aspect ratio.
    """
    img_width, img_height = image.size
    target_ratio = width_ratio / height_ratio
    current_ratio = img_width / img_height

    if current_ratio > target_ratio:
        # Image is wider than target ratio; crop width
        new_width = int(img_height * target_ratio)
        return center_crop(image, new_width, img_height)
    else:
        # Image is taller than target ratio; crop height
        new_height = int(img_width / target_ratio)
        return center_crop(image, img_width, new_height)


def crop_file(
    input_path: str,
    output_path: str,
    left: int,
    top: int,
    right: int,
    bottom: int,
) -> str:
    """Crop an image file to specified coordinates.

    Args:
        input_path: Path to input image.
        output_path: Path to save cropped image.
        left: Left coordinate.
        top: Top coordinate.
        right: Right coordinate.
        bottom: Bottom coordinate.

    Returns:
        Path to the output file.
    """
    with Image.open(input_path) as img:
        result = crop(img, left, top, right, bottom)
        result.save(output_path)
    return output_path
