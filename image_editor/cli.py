"""CLI entry point for image_editor."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
from click.core import ParameterSource

from image_editor import __version__
from image_editor.operations import (
    crop_file,
    resize_file,
    convert_file,
    background_file,
    crop_face_file,
    PRESET_SIZES,
    FORMAT_ALIASES,
)
from image_editor.settings import Settings
from image_editor.utils.batch import batch_process, find_images
from image_editor.utils.backup import create_backup


def _parse_color(color_str: str) -> tuple:
    """Parse a color string like '255,255,255' or '#ffffff' to an RGB tuple."""
    color_str = color_str.strip()
    if color_str.startswith("#"):
        h = color_str.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    parts = [int(x.strip()) for x in color_str.split(",")]
    if len(parts) != 3:
        raise ValueError(f"Invalid color format: {color_str!r}. Use '255,255,255' or '#ffffff'.")
    return tuple(parts)


# ---------------------------------------------------------------------------
# Global context object passed from the top-level group to sub-commands
# ---------------------------------------------------------------------------

class _Context:
    def __init__(self, settings: Settings):
        self.settings = settings


pass_ctx = click.make_pass_decorator(_Context, ensure=True)


@click.group()
@click.version_option(version=__version__, prog_name="image-editor")
@click.option(
    "--settings-file",
    "settings_file",
    default=None,
    envvar="IMAGE_EDITOR_SETTINGS",
    help=(
        "Path to a JSON settings file that provides default values for all "
        "options.  CLI flags always override settings file values.  "
        "Env var: IMAGE_EDITOR_SETTINGS."
    ),
    type=click.Path(exists=False),
)
@click.pass_context
def cli(ctx: click.Context, settings_file: Optional[str]):
    """image-editor: A versatile image and photo editing tool.

    Supports cropping, resizing, face detection, background removal,
    format conversion (including WebP and SVG), backup, and batch processing.

    Options can be provided directly on the command line **or** via a JSON
    settings file (use ``--settings-file path/to/settings.json``).

    Examples:

    \b
      image-editor --settings-file settings.json resize photo.jpg -o out.jpg
      image-editor crop photo.jpg -o out.jpg --left 10 --top 10 --right 400 --bottom 400
      image-editor resize photo.jpg -o out.jpg --width 800 --height 600
      image-editor resize photo.jpg -o out.jpg --preset passport
      image-editor convert photo.png -o out.svg
      image-editor background photo.jpg -o out.png --action remove --method grabcut
      image-editor face photo.jpg -o face.png --style real --padding 0.2
      image-editor batch resize ./photos/ -o ./resized/ --width 800 --height 600
    """
    settings = Settings.load(settings_file)
    ctx.obj = _Context(settings)
    ctx.ensure_object(_Context)


# ---------------------------------------------------------------------------
# crop
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("-o", "--output", required=True, help="Output file path.")
@click.option("--left", type=int, default=0, show_default=True, help="Left coordinate.")
@click.option("--top", type=int, default=0, show_default=True, help="Top coordinate.")
@click.option("--right", type=int, required=True, help="Right coordinate.")
@click.option("--bottom", type=int, required=True, help="Bottom coordinate.")
@click.option("--backup", is_flag=True, help="Backup original file before processing.")
@click.option("--backup-dir", default=None, help="Directory to store backups.")
@pass_ctx
def crop(ctx, input, output, left, top, right, bottom, backup, backup_dir):
    """Crop an image to specified coordinates.

    INPUT is the path to the input image.
    """
    s = ctx.settings
    if backup or s.get("backup_enabled"):
        bp = create_backup(input, backup_dir or s.get("backup_dir"))
        click.echo(f"Backup created: {bp}")
    crop_file(input, output, left, top, right, bottom)
    click.echo(f"Cropped image saved to: {output}")


# ---------------------------------------------------------------------------
# resize
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("-o", "--output", required=True, help="Output file path.")
@click.option("--width", type=int, default=0, help="Target width (0 = auto from height).")
@click.option("--height", type=int, default=0, help="Target height (0 = auto from width).")
@click.option(
    "--preset",
    type=click.Choice(list(PRESET_SIZES.keys())),
    default=None,
    help="Resize to a named preset.",
)
@click.option(
    "--keep-aspect",
    is_flag=True,
    help="Preserve aspect ratio (fit within width x height).",
)
@click.option("--backup", is_flag=True, help="Backup original file before processing.")
@click.option("--backup-dir", default=None, help="Directory to store backups.")
@pass_ctx
def resize(ctx, input, output, width, height, preset, keep_aspect, backup, backup_dir):
    """Resize an image to specified dimensions or a preset size.

    INPUT is the path to the input image.

    Available presets: passport, id_photo, business_card, a4, a5,
    instagram_square, instagram_portrait, twitter_header, facebook_cover,
    fullhd, 4k.

    The LANCZOS filter is used by default, which preserves image quality
    when downscaling.
    """
    s = ctx.settings
    if not preset and width <= 0 and height <= 0:
        raise click.UsageError("Specify --width, --height, or --preset.")
    if backup or s.get("backup_enabled"):
        bp = create_backup(input, backup_dir or s.get("backup_dir"))
        click.echo(f"Backup created: {bp}")
    resize_file(input, output, width, height, keep_aspect=keep_aspect, preset=preset)
    click.echo(f"Resized image saved to: {output}")


# ---------------------------------------------------------------------------
# convert
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("-o", "--output", required=True, help="Output file path.")
@click.option(
    "--format",
    "target_format",
    type=click.Choice(list(FORMAT_ALIASES.keys()) + ["PNG", "JPEG", "WEBP", "GIF", "BMP", "TIFF", "SVG"]),
    default=None,
    help="Target format (inferred from output extension if not specified). Use 'svg' for web SVG.",
)
@click.option(
    "--quality",
    type=click.IntRange(1, 95),
    default=95,
    show_default=True,
    help="Quality for JPEG/WebP output (1-95).",
)
@click.option(
    "--bg-color",
    default="255,255,255",
    show_default=True,
    help="Background color when removing transparency (e.g., '255,255,255' or '#ffffff').",
)
@click.option("--backup", is_flag=True, help="Backup original file before processing.")
@click.option("--backup-dir", default=None, help="Directory to store backups.")
@pass_ctx
def convert(ctx, input, output, target_format, quality, bg_color, backup, backup_dir):
    """Convert an image to a different format.

    INPUT is the path to the input image.

    Supports JPEG, PNG, WebP, GIF, BMP, TIFF, ICO, and SVG.
    SVG output embeds the raster image inside an SVG wrapper for web use.
    """
    s = ctx.settings
    bg = _parse_color(bg_color)
    effective_quality = quality if quality != 95 else s.get("jpeg_quality", 95)
    if backup or s.get("backup_enabled"):
        bp = create_backup(input, backup_dir or s.get("backup_dir"))
        click.echo(f"Backup created: {bp}")
    convert_file(input, output, target_format=target_format, quality=effective_quality, background_color=bg)
    click.echo(f"Converted image saved to: {output}")


# ---------------------------------------------------------------------------
# background
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("-o", "--output", required=True, help="Output file path.")
@click.option(
    "--action",
    type=click.Choice(["remove", "replace"]),
    default="remove",
    show_default=True,
    help="Background action: 'remove' (make transparent) or 'replace' (fill with color).",
)
@click.option(
    "--threshold",
    type=click.IntRange(0, 255),
    default=30,
    show_default=True,
    help="Color distance threshold for background detection (0-255). Used with --method flood.",
)
@click.option(
    "--color",
    default="255,255,255",
    show_default=True,
    help="Replacement background color (used with --action replace).",
)
@click.option(
    "--method",
    type=click.Choice(["flood", "grabcut", "rembg"]),
    default="flood",
    show_default=True,
    help=(
        "Segmentation method. 'flood' is fast and works on solid-colour backgrounds. "
        "'grabcut' uses edge-aware segmentation and works on complex backgrounds. "
        "'rembg' uses deep-learning (U\u00b2-Net) for highest accuracy person/object "
        "segmentation including hair edges and fine detail. "
        "Can also be set in a settings file via 'bg_method'."
    ),
)
@click.option(
    "--rembg-model",
    type=click.Choice(["u2net", "u2net_human_seg", "isnet-general-use"]),
    default="u2net",
    show_default=True,
    help="Model for rembg method. 'u2net_human_seg' is optimised for portraits.",
)
@click.option(
    "--alpha-matting",
    is_flag=True,
    default=False,
    help="Enable alpha matting for fine edge detail (rembg method only). Slower but better hair/fur edges.",
)
@click.option(
    "--grabcut-iterations",
    type=int,
    default=5,
    show_default=True,
    help="Number of GrabCut iterations (only used with --method grabcut).",
)
@click.option("--backup", is_flag=True, help="Backup original file before processing.")
@click.option("--backup-dir", default=None, help="Directory to store backups.")
@pass_ctx
@click.pass_context
def background(click_ctx, ctx, input, output, action, threshold, color, method, rembg_model, alpha_matting, grabcut_iterations, backup, backup_dir):
    """Process the background of an image.

    INPUT is the path to the input image.

    Use --action remove to make the background transparent (saves as PNG/WEBP).
    Use --action replace to replace the background with a solid color.

    Supports three methods:
    - flood: Fast, for solid-colour backgrounds
    - grabcut: Edge-aware OpenCV segmentation
    - rembg: Deep-learning (U\u00b2-Net) for highest quality person/object segmentation
    """
    s = ctx.settings
    src = click_ctx.get_parameter_source
    effective_method = method if src("method") != ParameterSource.DEFAULT else s.get("bg_method", "flood")
    effective_threshold = threshold if src("threshold") != ParameterSource.DEFAULT else s.get("bg_threshold", 30)
    bg_color = _parse_color(color)
    if backup or s.get("backup_enabled"):
        bp = create_backup(input, backup_dir or s.get("backup_dir"))
        click.echo(f"Backup created: {bp}")
    background_file(
        input, output,
        action=action,
        threshold=effective_threshold,
        color=bg_color,
        method=effective_method,
        grabcut_iterations=grabcut_iterations,
        rembg_model=rembg_model,
        alpha_matting=alpha_matting,
    )
    click.echo(f"Processed image saved to: {output}")


# ---------------------------------------------------------------------------
# face
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("-o", "--output", required=True, help="Output file path.")
@click.option(
    "--style",
    type=click.Choice(["real", "real_alt", "anime", "profile"]),
    default="real",
    show_default=True,
    help=(
        "Face detection style.  'real' = photographs / 3-D renders (default). "
        "'anime' = 2-D / cartoon / illustration faces. "
        "'profile' = side-facing real faces."
    ),
)
@click.option(
    "--padding",
    type=float,
    default=0.2,
    show_default=True,
    help="Fractional padding around the detected face (0.2 = 20 %% of face size).",
)
@click.option(
    "--min-size",
    type=int,
    default=30,
    show_default=True,
    help="Minimum face size in pixels.",
)
@click.option(
    "--face-index",
    type=int,
    default=0,
    show_default=True,
    help="Index of the face to crop (0 = largest detected face).",
)
@click.option("--backup", is_flag=True, help="Backup original file before processing.")
@click.option("--backup-dir", default=None, help="Directory to store backups.")
@pass_ctx
@click.pass_context
def face(click_ctx, ctx, input, output, style, padding, min_size, face_index, backup, backup_dir):
    """Detect and crop a face from an image.

    INPUT is the path to the input image.

    Uses OpenCV Haar Cascade classifiers – no separate model download required.
    Supports real photographs, 3-D renders, and 2-D/anime illustrations.
    """
    s = ctx.settings
    src = click_ctx.get_parameter_source
    effective_padding = padding if src("padding") != ParameterSource.DEFAULT else s.get("face_padding", 0.2)
    effective_min_size = min_size if src("min_size") != ParameterSource.DEFAULT else s.get("face_min_size", 30)
    if backup or s.get("backup_enabled"):
        bp = create_backup(input, backup_dir or s.get("backup_dir"))
        click.echo(f"Backup created: {bp}")
    try:
        crop_face_file(
            input, output,
            padding=effective_padding,
            style=style,
            min_size=effective_min_size,
            face_index=face_index,
        )
        click.echo(f"Face crop saved to: {output}")
    except ValueError as exc:
        raise click.ClickException(str(exc))


# ---------------------------------------------------------------------------
# batch
# ---------------------------------------------------------------------------

@cli.group()
def batch():
    """Batch process multiple images."""


@batch.command(name="crop")
@click.argument("input_dir", type=click.Path(exists=True, file_okay=False))
@click.option("-o", "--output-dir", required=True, help="Output directory.")
@click.option("--left", type=int, default=0, show_default=True)
@click.option("--top", type=int, default=0, show_default=True)
@click.option("--right", type=int, required=True)
@click.option("--bottom", type=int, required=True)
@click.option("--recursive", is_flag=True, help="Search subdirectories.")
@click.option("--backup", is_flag=True, help="Backup originals.")
@click.option("--backup-dir", default=None)
@click.option("--overwrite", is_flag=True, help="Overwrite existing output files.")
def batch_crop(input_dir, output_dir, left, top, right, bottom, recursive, backup, backup_dir, overwrite):
    """Batch crop images in a directory."""
    from image_editor.operations.crop import crop_file as _crop_file
    files = find_images(input_dir, recursive=recursive)
    if not files:
        click.echo("No image files found.")
        return
    click.echo(f"Processing {len(files)} file(s)...")
    results = batch_process(
        files,
        _crop_file,
        output_dir=output_dir,
        backup=backup,
        backup_dir=backup_dir,
        overwrite=overwrite,
        left=left,
        top=top,
        right=right,
        bottom=bottom,
    )
    _print_batch_results(results)


@batch.command(name="resize")
@click.argument("input_dir", type=click.Path(exists=True, file_okay=False))
@click.option("-o", "--output-dir", required=True, help="Output directory.")
@click.option("--width", type=int, default=0)
@click.option("--height", type=int, default=0)
@click.option("--preset", type=click.Choice(list(PRESET_SIZES.keys())), default=None)
@click.option("--keep-aspect", is_flag=True)
@click.option("--recursive", is_flag=True, help="Search subdirectories.")
@click.option("--backup", is_flag=True, help="Backup originals.")
@click.option("--backup-dir", default=None)
@click.option("--overwrite", is_flag=True, help="Overwrite existing output files.")
def batch_resize(input_dir, output_dir, width, height, preset, keep_aspect, recursive, backup, backup_dir, overwrite):
    """Batch resize images in a directory."""
    from image_editor.operations.resize import resize_file as _resize_file
    if not preset and width <= 0 and height <= 0:
        raise click.UsageError("Specify --width, --height, or --preset.")
    files = find_images(input_dir, recursive=recursive)
    if not files:
        click.echo("No image files found.")
        return
    click.echo(f"Processing {len(files)} file(s)...")
    results = batch_process(
        files,
        _resize_file,
        output_dir=output_dir,
        backup=backup,
        backup_dir=backup_dir,
        overwrite=overwrite,
        width=width,
        height=height,
        keep_aspect=keep_aspect,
        preset=preset,
    )
    _print_batch_results(results)


@batch.command(name="convert")
@click.argument("input_dir", type=click.Path(exists=True, file_okay=False))
@click.option("-o", "--output-dir", required=True, help="Output directory.")
@click.option(
    "--format",
    "target_format",
    type=click.Choice(list(FORMAT_ALIASES.keys()) + ["PNG", "JPEG", "WEBP", "GIF", "BMP", "TIFF"]),
    required=True,
    help="Target format.",
)
@click.option("--quality", type=click.IntRange(1, 95), default=95)
@click.option("--recursive", is_flag=True, help="Search subdirectories.")
@click.option("--backup", is_flag=True, help="Backup originals.")
@click.option("--backup-dir", default=None)
@click.option("--overwrite", is_flag=True, help="Overwrite existing output files.")
def batch_convert(input_dir, output_dir, target_format, quality, recursive, backup, backup_dir, overwrite):
    """Batch convert images in a directory to a target format."""
    from image_editor.operations.convert import convert_file as _convert_file
    from image_editor.operations.convert import normalize_format
    files = find_images(input_dir, recursive=recursive)
    if not files:
        click.echo("No image files found.")
        return
    click.echo(f"Processing {len(files)} file(s)...")
    fmt = normalize_format(target_format)
    ext = target_format.lower().lstrip(".")
    results = batch_process(
        files,
        _convert_file,
        output_dir=output_dir,
        output_format=ext,
        backup=backup,
        backup_dir=backup_dir,
        overwrite=overwrite,
        target_format=fmt,
        quality=quality,
    )
    _print_batch_results(results)


@batch.command(name="background")
@click.argument("input_dir", type=click.Path(exists=True, file_okay=False))
@click.option("-o", "--output-dir", required=True, help="Output directory.")
@click.option("--action", type=click.Choice(["remove", "replace"]), default="remove")
@click.option("--threshold", type=click.IntRange(0, 255), default=30)
@click.option("--color", default="255,255,255")
@click.option("--recursive", is_flag=True, help="Search subdirectories.")
@click.option("--backup", is_flag=True, help="Backup originals.")
@click.option("--backup-dir", default=None)
@click.option("--overwrite", is_flag=True, help="Overwrite existing output files.")
def batch_background(input_dir, output_dir, action, threshold, color, recursive, backup, backup_dir, overwrite):
    """Batch process backgrounds of images in a directory."""
    from image_editor.operations.background import background_file as _background_file
    bg_color = _parse_color(color)
    files = find_images(input_dir, recursive=recursive)
    if not files:
        click.echo("No image files found.")
        return
    click.echo(f"Processing {len(files)} file(s)...")
    out_fmt = "png" if action == "remove" else None
    results = batch_process(
        files,
        _background_file,
        output_dir=output_dir,
        output_format=out_fmt,
        backup=backup,
        backup_dir=backup_dir,
        overwrite=overwrite,
        action=action,
        threshold=threshold,
        color=bg_color,
    )
    _print_batch_results(results)


def _print_batch_results(results: list) -> None:
    """Print batch processing results summary."""
    ok = sum(1 for r in results if r["status"] == "ok")
    skipped = sum(1 for r in results if r["status"].startswith("skipped"))
    errors = sum(1 for r in results if r["status"].startswith("error"))

    for r in results:
        status = r["status"]
        if status.startswith("error"):
            click.echo(f"  ERROR  {r['input']}: {status}", err=True)
        elif status.startswith("skipped"):
            click.echo(f"  SKIP   {r['input']}")
        else:
            click.echo(f"  OK     {r['output']}")

    click.echo(f"\nDone: {ok} processed, {skipped} skipped, {errors} errors.")


def main():
    """CLI entry point."""
    cli()


if __name__ == "__main__":
    main()
