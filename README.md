# image_editor

画像・写真加工ツール — A versatile image and photo editing GUI/CLI tool.

## Features

- **Crop** — Crop images to specified coordinates or aspect ratios
- **Resize** — Resize to custom dimensions or named photo presets (passport, A4, Instagram, etc.)
- **Background removal** — Make backgrounds transparent using flood-fill detection
- **Background replacement** — Replace the background with a solid color
- **Format conversion** — Convert between JPEG, PNG, WebP, GIF, BMP, TIFF, and more
- **Batch processing** — Apply any operation to an entire directory of images at once
- **Backup** — Automatically back up originals before processing
- **GUI** — Full graphical interface built with tkinter
- **CLI** — Full command-line interface built with Click

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## CLI Usage

```bash
# Show help
image-editor --help

# Crop
image-editor crop photo.jpg -o out.jpg --left 10 --top 10 --right 400 --bottom 400

# Resize to custom dimensions
image-editor resize photo.jpg -o out.jpg --width 800 --height 600

# Resize to a preset (preserving aspect ratio with padding)
image-editor resize photo.jpg -o out.jpg --preset passport --keep-aspect

# Convert format
image-editor convert photo.png -o out.jpg --quality 90

# Remove background (make transparent)
image-editor background photo.jpg -o out.png --action remove --threshold 30

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
- **Convert** — Choose target format and quality
- **Background** — Remove or replace the background
- **Batch** — Process an entire directory
- **Preview** — Preview the loaded or output image

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Project Structure

```
image_editor/
├── image_editor/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point (Click)
│   ├── gui.py              # GUI entry point (tkinter)
│   ├── operations/
│   │   ├── crop.py         # Crop operations
│   │   ├── resize.py       # Resize operations
│   │   ├── convert.py      # Format conversion
│   │   └── background.py   # Background removal/replacement
│   └── utils/
│       ├── backup.py       # Backup utilities
│       └── batch.py        # Batch processing utilities
├── tests/                  # pytest test suite
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

## License

MIT
