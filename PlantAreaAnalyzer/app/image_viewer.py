from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QSizePolicy,
)


class ImageViewer(QGraphicsView):
    """Image viewer with wheel zoom, drag panning, and double-click reset."""

    def __init__(self, placeholder_text: str) -> None:
        super().__init__()
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(
            "QGraphicsView { background-color: #f3f5f7; border: 1px solid #c7d0d9; }"
        )
        self.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setToolTip(
            "Mausrad: zoomen | Ziehen: Ausschnitt verschieben | Doppelklick: anpassen"
        )

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._pixmap: Optional[QPixmap] = None
        self._placeholder_text = placeholder_text
        self._zoom_factor = 1.0
        self._show_placeholder()

    def set_image(self, image: QImage) -> None:
        old_size = self._pixmap.size() if self._pixmap else None
        was_zoomed = self._zoom_factor > 1.01
        self._pixmap = QPixmap.fromImage(image)

        if self._pixmap_item is None:
            self._scene.clear()
            self._pixmap_item = self._scene.addPixmap(self._pixmap)
        else:
            self._pixmap_item.setPixmap(self._pixmap)

        self._scene.setSceneRect(QRectF(self._pixmap.rect()))

        if not was_zoomed or old_size != self._pixmap.size():
            self.reset_zoom()

    def clear_image(self, text: Optional[str] = None) -> None:
        self._pixmap = None
        if text:
            self._placeholder_text = text
        self._show_placeholder()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if self._pixmap and self._zoom_factor <= 1.01:
            self.reset_zoom()

    def wheelEvent(self, event) -> None:  # type: ignore[override]
        if not self._pixmap:
            return

        zoom_step = 1.18 if event.angleDelta().y() > 0 else 1 / 1.18
        next_zoom = self._zoom_factor * zoom_step
        if next_zoom < 1.0:
            self.reset_zoom()
            return
        if next_zoom > 12.0:
            return

        self._zoom_factor = next_zoom
        self.scale(zoom_step, zoom_step)

    def mouseDoubleClickEvent(self, event) -> None:  # type: ignore[override]
        if self._pixmap:
            self.reset_zoom()
        super().mouseDoubleClickEvent(event)

    def reset_zoom(self) -> None:
        if not self._pixmap_item:
            return

        self.resetTransform()
        self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)
        self._zoom_factor = 1.0

    def _show_placeholder(self) -> None:
        self._scene.clear()
        self._pixmap_item = None
        self._zoom_factor = 1.0
        self._scene.addText(self._placeholder_text)
