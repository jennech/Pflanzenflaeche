from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QSizePolicy,
)


class ImageViewer(QGraphicsView):
    """Image viewer with wheel zoom, drag panning, and double-click reset."""

    circle_selected = Signal(object)

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
        self._circle_item: Optional[QGraphicsEllipseItem] = None
        self._pixmap: Optional[QPixmap] = None
        self._placeholder_text = placeholder_text
        self._zoom_factor = 1.0
        self._circle_visible = False
        self._manual_circle_enabled = False
        self._drag_start: Optional[QPointF] = None
        self._show_placeholder()

    def set_image(self, image: QImage) -> None:
        old_size = self._pixmap.size() if self._pixmap else None
        was_zoomed = self._zoom_factor > 1.01
        self._pixmap = QPixmap.fromImage(image)

        if self._pixmap_item is None:
            self._scene.clear()
            self._circle_item = None
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

    def set_petri_circle(
        self,
        circle: tuple[int, int, int] | None,
        visible: bool,
    ) -> None:
        self._circle_visible = visible
        if circle is None or self._pixmap_item is None:
            self._remove_circle()
            return

        center_x, center_y, radius = circle
        rect = QRectF(
            center_x - radius,
            center_y - radius,
            radius * 2,
            radius * 2,
        )
        if self._circle_item is None:
            pen = QPen(QColor(255, 190, 0), 3)
            self._circle_item = self._scene.addEllipse(rect, pen)
            self._circle_item.setZValue(10)
        else:
            self._circle_item.setRect(rect)

        self._circle_item.setVisible(visible)

    def set_petri_overlay_visible(self, visible: bool) -> None:
        self._circle_visible = visible
        if self._circle_item is not None:
            self._circle_item.setVisible(visible)

    def set_manual_circle_enabled(self, enabled: bool) -> None:
        self._manual_circle_enabled = enabled
        self.setDragMode(
            QGraphicsView.NoDrag if enabled else QGraphicsView.ScrollHandDrag
        )
        if enabled:
            self.setToolTip("Kreis aufziehen: Mittelpunkt und Radius der Petrischale setzen")
        else:
            self.setToolTip(
                "Mausrad: zoomen | Ziehen: Ausschnitt verschieben | Doppelklick: anpassen"
            )

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

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if self._manual_circle_enabled and self._pixmap:
            self._drag_start = self.mapToScene(event.position().toPoint())
            self.set_petri_circle(
                (int(self._drag_start.x()), int(self._drag_start.y()), 1),
                True,
            )
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._manual_circle_enabled and self._drag_start is not None:
            current = self.mapToScene(event.position().toPoint())
            radius = max(1, int(round(distance_between(self._drag_start, current))))
            self.set_petri_circle(
                (int(self._drag_start.x()), int(self._drag_start.y()), radius),
                True,
            )
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        if self._manual_circle_enabled and self._drag_start is not None:
            current = self.mapToScene(event.position().toPoint())
            radius = max(1, int(round(distance_between(self._drag_start, current))))
            circle = (
                int(self._drag_start.x()),
                int(self._drag_start.y()),
                radius,
            )
            self._drag_start = None
            self.set_petri_circle(circle, True)
            self.circle_selected.emit(circle)
            return
        super().mouseReleaseEvent(event)

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
        self._circle_item = None
        self._zoom_factor = 1.0
        self._scene.addText(self._placeholder_text)

    def _remove_circle(self) -> None:
        if self._circle_item is not None:
            self._scene.removeItem(self._circle_item)
            self._circle_item = None


def distance_between(first: QPointF, second: QPointF) -> float:
    delta_x = first.x() - second.x()
    delta_y = first.y() - second.y()
    return (delta_x * delta_x + delta_y * delta_y) ** 0.5
