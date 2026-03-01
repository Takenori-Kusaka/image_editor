# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
