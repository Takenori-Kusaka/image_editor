# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **rembg background removal** – New `rembg` method for background removal/replacement
  using deep-learning segmentation (U²-Net). Provides significantly higher accuracy
  for person/object segmentation compared to GrabCut, including fine details like
  hair edges, clothing, and semi-transparent regions.
  - Three model options: `u2net` (general), `u2net_human_seg` (portraits),
    `isnet-general-use` (high quality).
  - Optional alpha matting for finer edge detail.
  - CLI: `--method rembg`, `--rembg-model`, `--alpha-matting` options.
  - GUI: "rembg" added to background method dropdown.
- **Release workflow** – `.github/workflows/release.yml` builds standalone binaries
  for Windows, macOS, and Linux via PyInstaller and publishes them as GitHub Releases
  when a version tag (`v*`) is pushed.
- **Rule files** – `rules/` directory with JSON templates for Japanese ID photo
  specifications: マイナンバーカード, パスポート, 履歴書, 運転免許証.
  Each file contains print/digital specs, face positioning guides, and
  `image_editor_settings` ready for use.
- **Crop presets** – Added `mynumber`, `resume`, and `drivers_license` to
  `PRESET_SIZES` in `crop.py`.

### Changed
- **CI** – Test matrix now includes macOS and Windows in addition to Ubuntu.
- **CLI** – Fixed settings-file override logic: explicitly provided CLI flags now always
  take precedence over settings file defaults (uses `ParameterSource` instead of
  value comparison).
- **pyproject.toml** – Added project metadata: authors, keywords, classifiers, and
  project URLs for PyPI and GitHub.
- **.gitignore** – Extended to cover `coverage.xml`, `*.spec`, OS junk files, and
  temporary files.
- **Dependencies** – Added `rembg[cpu]>=2.0.50` as a project dependency.

## [0.1.0] - 2026-03-01

### Added
- **Crop** – coordinate, center, and aspect-ratio crop operations.
- **Resize** – custom dimensions, auto-aspect, or named photo presets (passport, A4, Instagram, 4K, etc.) using the high-quality LANCZOS filter.
- **Face detection & crop** – OpenCV Haar Cascade classifiers; supports real photographs, 3-D renders, and 2-D/anime illustrations (`--style anime`).
- **Background removal & replacement** – two methods:
  - `flood` – fast flood-fill from image corners, ideal for solid-colour backgrounds.
  - `grabcut` – OpenCV GrabCut edge-aware segmentation for complex backgrounds and all image styles.
- **Format conversion** – JPEG, PNG, WebP, GIF, BMP, TIFF, ICO, and **SVG** (raster image embedded in SVG wrapper).
- **Backup** – automatic timestamped backup before any destructive operation.
- **Batch processing** – apply any operation to an entire directory with recursive search, overwrite control, and per-file backup.
- **CLI** – `image-editor` command with `--settings-file` option for externalized configuration.
- **GUI** – `image-editor-gui` command (tkinter) with persistent settings.
- **Settings** – JSON-based external settings (`settings.py`) loaded at startup; all options persist between sessions.
- **GitHub Actions CI** – matrix test across Python 3.9 – 3.12.
- **MIT License**.
