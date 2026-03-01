"""CLI entry point for image_editor."""

import sys
from pathlib import Path

import click

from image_editor import __version__
from image_editor.operations import (
    crop_file,
    resize_file,
    convert_file,
    background_file,
    PRESET_SIZES,
    FORMAT_ALIASES,
)
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


@click.group()
@click.version_option(version=__version__, prog_name="image-editor")
def cli():
    """image-editor: A versatile image and photo editing tool.

    Supports cropping, resizing, background removal, format conversion,
    backup, and batch processing.

    Examples:

    \b
      image-editor crop photo.jpg -o out.jpg --left 10 --top 10 --right 400 --bottom 400
      image-editor resize photo.jpg -o out.jpg --width 800 --height 600
      image-editor resize photo.jpg -o out.jpg --preset passport
      image-editor convert photo.png -o out.jpg
      image-editor background photo.jpg -o out.png --action remove
      image-editor batch resize ./photos/ -o ./resized/ --width 800 --height 600
    """


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
def crop(input, output, left, top, right, bottom, backup, backup_dir):
    """Crop an image to specified coordinates.

    INPUT is the path to the input image.
    """
    if backup:
        bp = create_backup(input, backup_dir)
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
def resize(input, output, width, height, preset, keep_aspect, backup, backup_dir):
    """Resize an image to specified dimensions or a preset size.

    INPUT is the path to the input image.

    Available presets: passport, id_photo, business_card, a4, a5,
    instagram_square, instagram_portrait, twitter_header, facebook_cover,
    fullhd, 4k.
    """
    if not preset and width <= 0 and height <= 0:
        raise click.UsageError("Specify --width, --height, or --preset.")
    if backup:
        bp = create_backup(input, backup_dir)
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
    type=click.Choice(list(FORMAT_ALIASES.keys()) + ["PNG", "JPEG", "WEBP", "GIF", "BMP", "TIFF"]),
    default=None,
    help="Target format (inferred from output extension if not specified).",
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
def convert(input, output, target_format, quality, bg_color, backup, backup_dir):
    """Convert an image to a different format.

    INPUT is the path to the input image.
    """
    bg = _parse_color(bg_color)
    if backup:
        bp = create_backup(input, backup_dir)
        click.echo(f"Backup created: {bp}")
    convert_file(input, output, target_format=target_format, quality=quality, background_color=bg)
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
    help="Color distance threshold for background detection (0-255).",
)
@click.option(
    "--color",
    default="255,255,255",
    show_default=True,
    help="Replacement background color (used with --action replace).",
)
@click.option("--backup", is_flag=True, help="Backup original file before processing.")
@click.option("--backup-dir", default=None, help="Directory to store backups.")
def background(input, output, action, threshold, color, backup, backup_dir):
    """Process the background of an image.

    INPUT is the path to the input image.

    Use --action remove to make the background transparent (saves as PNG/WEBP).
    Use --action replace to replace the background with a solid color.
    """
    bg_color = _parse_color(color)
    if backup:
        bp = create_backup(input, backup_dir)
        click.echo(f"Backup created: {bp}")
    background_file(input, output, action=action, threshold=threshold, color=bg_color)
    click.echo(f"Processed image saved to: {output}")


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
