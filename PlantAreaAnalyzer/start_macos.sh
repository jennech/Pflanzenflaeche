#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"
source .venv313/bin/activate

unset QT_PLUGIN_PATH
unset QT_QPA_PLATFORM_PLUGIN_PATH
export QT_QPA_PLATFORM=cocoa

python main.py
