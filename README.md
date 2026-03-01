# image_editor

[![CI](https://github.com/Takenori-Kusaka/image_editor/actions/workflows/ci.yml/badge.svg)](https://github.com/Takenori-Kusaka/image_editor/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

画像・写真加工ツール — A versatile image and photo editing GUI/CLI tool.

## Features

- **Crop** — Crop images to specified coordinates or aspect ratios
- **Resize** — Resize with high-quality LANCZOS resampling; custom dimensions or named photo presets (passport, A4, Instagram, 4K, etc.)
- **Face detection & crop** — Detect and crop faces using OpenCV Haar Cascades; supports real photographs, 3-D renders, and 2-D/anime illustrations
- **Background removal** — Two methods:
  - `flood` — Fast flood-fill from image corners (solid-colour backgrounds)
  - `grabcut` — OpenCV GrabCut edge-aware segmentation for complex backgrounds and all art styles
- **Background replacement** — Replace the detected background with any solid colour
- **Format conversion** — Convert between JPEG, PNG, **WebP**, **SVG**, GIF, BMP, TIFF, ICO
- **Batch processing** — Apply any operation to an entire directory (recursive, overwrite control)
- **Backup** — Automatically back up originals before processing
- **External settings** — Load defaults from a JSON `settings.json` file (persists between sessions)
- **GUI** — Full graphical interface (tkinter) with persistent settings
- **CLI** — Full command-line interface with `--settings-file` support

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## CLI Usage

```bash
# Show help
image-editor --help

# Use a settings file for default values
image-editor --settings-file settings.json resize photo.jpg -o out.jpg

# Crop
image-editor crop photo.jpg -o out.jpg --left 10 --top 10 --right 400 --bottom 400

# Resize to custom dimensions
image-editor resize photo.jpg -o out.jpg --width 800 --height 600

# Resize to a preset (preserving aspect ratio with padding)
image-editor resize photo.jpg -o out.jpg --preset passport --keep-aspect

# Convert to WebP
image-editor convert photo.png -o out.webp

# Convert to SVG (raster embedded in SVG wrapper for web use)
image-editor convert photo.png -o out.svg

# Detect and crop a face (real photo / 3-D render)
image-editor face photo.jpg -o face.png --style real --padding 0.2

# Detect and crop a face from a 2-D / anime illustration
image-editor face illustration.png -o face.png --style anime

# Remove background – fast flood-fill (solid-colour backgrounds)
image-editor background photo.jpg -o out.png --action remove --method flood

# Remove background – edge-aware GrabCut (complex backgrounds, all styles)
image-editor background photo.jpg -o out.png --action remove --method grabcut

# Replace background with a new color
image-editor background photo.jpg -o out.jpg --action replace --color 0,0,255

# Batch resize a directory
image-editor batch resize ./photos/ -o ./resized/ --width 800 --height 600

# Batch convert to WebP
image-editor batch convert ./photos/ -o ./webp/ --format webp

# Batch remove backgrounds
image-editor batch background ./photos/ -o ./transparent/ --action remove

# With backup
image-editor resize photo.jpg -o out.jpg --width 800 --height 600 --backup
```

### Settings File

All CLI options can be provided via a JSON settings file.  This allows
re-using the same configuration without repeating flags:

```json
{
  "jpeg_quality": 85,
  "bg_threshold": 25,
  "bg_method": "grabcut",
  "face_padding": 0.25,
  "backup_enabled": true,
  "backup_dir": "~/backups"
}
```

```bash
image-editor --settings-file settings.json resize photo.jpg -o out.jpg --width 800
```

The environment variable `IMAGE_EDITOR_SETTINGS` can also be used instead of the `--settings-file` flag.

### Available Presets

| Preset | Size (px) | Description |
|---|---|---|
| `passport` | 413×531 | 35×45mm @ 300dpi |
| `id_photo` | 600×800 | 3×4cm @ 200dpi |
| `business_card` | 1063×591 | 91×55mm @ 300dpi |
| `a4` | 2480×3508 | A4 @ 300dpi |
| `a5` | 1748×2480 | A5 @ 300dpi |
| `instagram_square` | 1080×1080 | Instagram square |
| `instagram_portrait` | 1080×1350 | Instagram portrait |
| `twitter_header` | 1500×500 | Twitter header |
| `facebook_cover` | 820×312 | Facebook cover |
| `fullhd` | 1920×1080 | Full HD |
| `4k` | 3840×2160 | 4K UHD |

## GUI Usage

```bash
image-editor-gui
```

The GUI provides tabs for each operation:

- **Crop** — Enter coordinates and click Crop
- **Resize** — Enter dimensions or choose a preset
- **Convert** — Choose target format (including SVG and WebP) and quality
- **Background** — Remove or replace the background (flood or GrabCut method)
- **Batch** — Process an entire directory
- **Preview** — Preview the loaded or output image

Settings are automatically loaded from `~/.config/image_editor/settings.json` on
startup and saved on exit, so the GUI remembers your preferences.

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Tests are organised into three levels:

| File | Level |
|---|---|
| `test_crop`, `test_resize`, `test_convert`, `test_background`, `test_face`, `test_backup`, `test_batch`, `test_settings` | Unit |
| `test_integration` | Integration |
| `test_e2e` | End-to-end (CLI) |

## Project Structure

```
image_editor/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI (Python 3.9–3.12)
├── image_editor/
│   ├── __init__.py
│   ├── cli.py                  # CLI entry point (Click + --settings-file)
│   ├── gui.py                  # GUI entry point (tkinter, persistent settings)
│   ├── settings.py             # External JSON settings management
│   ├── operations/
│   │   ├── crop.py             # Crop operations
│   │   ├── resize.py           # Resize with LANCZOS filter
│   │   ├── convert.py          # Format conversion incl. SVG export
│   │   ├── background.py       # Flood-fill + GrabCut background removal
│   │   └── face.py             # OpenCV Haar Cascade face detection/crop
│   └── utils/
│       ├── backup.py           # Timestamped backup utilities
│       └── batch.py            # Batch directory processing
├── tests/
│   ├── conftest.py
│   ├── test_crop.py            # Unit
│   ├── test_resize.py          # Unit
│   ├── test_convert.py         # Unit
│   ├── test_background.py      # Unit
│   ├── test_face.py            # Unit
│   ├── test_backup.py          # Unit
│   ├── test_batch.py           # Unit
│   ├── test_settings.py        # Unit
│   ├── test_cli.py             # Unit (CLI)
│   ├── test_integration.py     # Integration
│   └── test_e2e.py             # End-to-end (CLI)
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE                     # MIT
├── README.md
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

## License

MIT
