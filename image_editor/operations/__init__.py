"""Operations package for image_editor."""

from image_editor.operations.crop import (
    crop,
    center_crop,
    crop_to_aspect_ratio,
    crop_file,
    PRESET_SIZES,
)
from image_editor.operations.resize import (
    resize,
    resize_to_preset,
    resize_file,
)
from image_editor.operations.convert import (
    convert,
    convert_file,
    normalize_format,
    FORMAT_ALIASES,
    _image_to_svg,
)
from image_editor.operations.background import (
    remove_background_color,
    replace_background,
    make_transparent,
    background_file,
    remove_background_grabcut,
    replace_background_grabcut,
    remove_background_rembg,
    replace_background_rembg,
)
from image_editor.operations.face import (
    detect_faces,
    crop_face,
    crop_face_file,
)

__all__ = [
    "crop",
    "center_crop",
    "crop_to_aspect_ratio",
    "crop_file",
    "PRESET_SIZES",
    "resize",
    "resize_to_preset",
    "resize_file",
    "convert",
    "convert_file",
    "normalize_format",
    "FORMAT_ALIASES",
    "_image_to_svg",
    "remove_background_color",
    "replace_background",
    "make_transparent",
    "background_file",
    "remove_background_grabcut",
    "replace_background_grabcut",
    "remove_background_rembg",
    "replace_background_rembg",
    "detect_faces",
    "crop_face",
    "crop_face_file",
]
