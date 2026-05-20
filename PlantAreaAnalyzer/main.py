from __future__ import annotations

import os
from pathlib import Path

import PySide6


def configure_qt_plugins() -> None:
    """Help Qt find the macOS platform plugin inside the local venv."""

    pyside_dir = Path(PySide6.__file__).resolve().parent
    plugin_dir = pyside_dir / "Qt" / "plugins"
    platform_dir = plugin_dir / "platforms"

    if platform_dir.exists():
        os.environ.setdefault("QT_PLUGIN_PATH", str(plugin_dir))
        os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(platform_dir))


configure_qt_plugins()

from app.main_window import run  # noqa: E402


if __name__ == "__main__":
    run()
