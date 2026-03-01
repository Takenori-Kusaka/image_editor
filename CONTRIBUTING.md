# Contributing to image_editor

Thank you for considering contributing to **image_editor**! 🎉

## Code of Conduct

Please be respectful and constructive in all interactions.

## How to Contribute

### Reporting Bugs

Open an issue on GitHub with:
- A clear description of the bug
- Steps to reproduce
- Expected vs. actual behaviour
- Python version and OS

### Suggesting Features

Open an issue with the `enhancement` label and describe the feature and its use case.

### Pull Requests

1. **Fork** the repository and create a branch from `main`.
2. **Install** development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   ```
3. **Write tests** for any new functionality.
4. **Run the full test suite** and ensure all tests pass:
   ```bash
   python -m pytest tests/ -v
   ```
5. **Open a pull request** against `main` with a clear description of your changes.

## Project Structure

```
image_editor/
├── image_editor/
│   ├── __init__.py
│   ├── cli.py              # CLI (Click)
│   ├── gui.py              # GUI (tkinter)
│   ├── settings.py         # External JSON settings
│   ├── operations/
│   │   ├── crop.py
│   │   ├── resize.py
│   │   ├── convert.py      # including SVG export
│   │   ├── background.py   # flood-fill + GrabCut
│   │   └── face.py         # OpenCV Haar Cascade
│   └── utils/
│       ├── backup.py
│       └── batch.py
└── tests/
    ├── test_crop.py
    ├── test_resize.py
    ├── test_convert.py
    ├── test_background.py
    ├── test_face.py
    ├── test_backup.py
    ├── test_batch.py
    ├── test_settings.py
    ├── test_cli.py
    ├── test_integration.py  # integration tests
    └── test_e2e.py          # end-to-end CLI tests
```

## Testing

Tests are written with `pytest` and are organized into three levels:

| File | Level |
|---|---|
| `test_*.py` (operations, settings, backup, batch) | Unit |
| `test_integration.py` | Integration |
| `test_e2e.py` | End-to-end (CLI) |

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
