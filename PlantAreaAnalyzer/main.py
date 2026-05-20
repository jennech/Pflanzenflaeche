from __future__ import annotations

import os
import shutil
from pathlib import Path

import PySide6


def mirror_qt_plugins(plugin_dir: Path) -> Path:
    """Mirror Qt plugins to a simple path that Qt can enumerate on macOS 26."""

    mirror_dir = Path("/private/tmp/plantarea_qt_plugins_runtime")
    for source_path in plugin_dir.rglob("*"):
        target_path = mirror_dir / source_path.relative_to(plugin_dir)
        if source_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
        elif source_path.is_file():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(source_path, target_path)
    return mirror_dir


def configure_qt_plugins() -> None:
    """Help Qt find the macOS platform plugin inside the local venv."""

    pyside_dir = Path(PySide6.__file__).resolve().parent
    plugin_dir = pyside_dir / "Qt" / "plugins"

    if plugin_dir.exists():
        search_dir = mirror_qt_plugins(plugin_dir)
        os.environ["QT_PLUGIN_PATH"] = os.pathsep.join(
            [str(search_dir), str(plugin_dir)]
        )
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(search_dir / "platforms")
        os.environ.setdefault("QT_QPA_PLATFORM", "cocoa")


configure_qt_plugins()

from app.main_window import run  # noqa: E402


if __name__ == "__main__":
    run()
