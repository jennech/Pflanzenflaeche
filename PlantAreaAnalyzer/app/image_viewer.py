from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy


class ImageViewer(QLabel):
    """Simple image viewer that keeps aspect ratio on resize."""

    def __init__(self, placeholder_text: str) -> None:
        super().__init__(placeholder_text)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(
            "QLabel { background-color: #f3f5f7; border: 1px solid #c7d0d9; }"
        )
        self._pixmap: Optional[QPixmap] = None

    def set_image(self, image: QImage) -> None:
        self._pixmap = QPixmap.fromImage(image)
        self._update_scaled_pixmap()

    def clear_image(self, text: Optional[str] = None) -> None:
        self._pixmap = None
        self.clear()
        if text:
            self.setText(text)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self) -> None:
        if not self._pixmap:
            return

        scaled = self._pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.setPixmap(scaled)
