#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"
source .venv313/bin/activate

export QT_PLUGIN_PATH="$PWD/.venv313/lib/python3.13/site-packages/PySide6/Qt/plugins"
export QT_QPA_PLATFORM_PLUGIN_PATH="$QT_PLUGIN_PATH/platforms"

python main.py
