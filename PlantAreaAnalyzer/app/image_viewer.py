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
    point_selected = Signal(object)
    add_point_selected = Signal(object)

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
        self._inner_circle_item: Optional[QGraphicsEllipseItem] = None
        self._exclusion_items: list[QGraphicsEllipseItem] = []
        self._addition_items: list[QGraphicsEllipseItem] = []
        self._pixmap: Optional[QPixmap] = None
        self._placeholder_text = placeholder_text
        self._zoom_factor = 1.0
        self._circle_visible = False
        self._manual_circle_enabled = False
        self._exclusion_mode_enabled = False
        self._addition_mode_enabled = False
        self._drag_start: Optional[QPointF] = None
        self._pending_circle_center: Optional[QPointF] = None
        self._show_placeholder()

    def set_image(self, image: QImage) -> None:
        old_size = self._pixmap.size() if self._pixmap else None
        was_zoomed = self._zoom_factor > 1.01
        self._pixmap = QPixmap.fromImage(image)

        if self._pixmap_item is None:
            self._scene.clear()
            self._circle_item = None
            self._inner_circle_item = None
            self._exclusion_items = []
            self._addition_items = []
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

    def set_analysis_circle(
        self,
        circle: tuple[int, int, int] | None,
        visible: bool,
    ) -> None:
        if circle is None or self._pixmap_item is None:
            self._remove_inner_circle()
            return

        center_x, center_y, radius = circle
        rect = QRectF(
            center_x - radius,
            center_y - radius,
            radius * 2,
            radius * 2,
        )
        if self._inner_circle_item is None:
            pen = QPen(QColor(0, 170, 255), 2)
            pen.setStyle(Qt.DashLine)
            self._inner_circle_item = self._scene.addEllipse(rect, pen)
            self._inner_circle_item.setZValue(11)
        else:
            self._inner_circle_item.setRect(rect)

        self._inner_circle_item.setVisible(visible)

    def set_exclusion_points(self, points: list[tuple[int, int]]) -> None:
        self._clear_exclusion_points()
        if self._pixmap_item is None:
            return

        pen = QPen(QColor(255, 40, 40), 3)
        for center_x, center_y in points:
            rect = QRectF(center_x - 5, center_y - 5, 10, 10)
            item = self._scene.addEllipse(rect, pen)
            item.setZValue(20)
            self._exclusion_items.append(item)

    def set_addition_points(
        self,
        points: list[tuple[int, int]],
        radius_px: int = 14,
    ) -> None:
        patches = [(point_x, point_y, radius_px) for point_x, point_y in points]
        self.set_addition_patches(patches)

    def set_addition_patches(self, patches: list[tuple[int, int, int]]) -> None:
        self._clear_addition_points()
        if self._pixmap_item is None:
            return

        pen = QPen(QColor(0, 210, 120), 3)
        for center_x, center_y, radius_px in patches:
            radius = max(1, int(radius_px))
            rect = QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2)
            item = self._scene.addEllipse(rect, pen)
            item.setZValue(21)
            self._addition_items.append(item)

    def set_petri_overlay_visible(self, visible: bool) -> None:
        self._circle_visible = visible
        if self._circle_item is not None:
            self._circle_item.setVisible(visible)
        if self._inner_circle_item is not None:
            self._inner_circle_item.setVisible(visible)

    def set_manual_circle_enabled(self, enabled: bool) -> None:
        self._manual_circle_enabled = enabled
        self._drag_start = None
        self._pending_circle_center = None
        self.setDragMode(
            QGraphicsView.NoDrag
            if enabled or self._exclusion_mode_enabled or self._addition_mode_enabled
            else QGraphicsView.ScrollHandDrag
        )
        if enabled:
            self.setToolTip(
                "Trackpad: 1. Tap Mitte | 2. Tap Rand | Alternativ: Kreis ziehen"
            )
        else:
            self.setToolTip(
                "Mausrad: zoomen | Ziehen: Ausschnitt verschieben | Doppelklick: anpassen"
            )

    def set_exclusion_mode_enabled(self, enabled: bool) -> None:
        self._exclusion_mode_enabled = enabled
        self._drag_start = None
        self._pending_circle_center = None
        self.setDragMode(
            QGraphicsView.NoDrag
            if enabled or self._manual_circle_enabled or self._addition_mode_enabled
            else QGraphicsView.ScrollHandDrag
        )
        if enabled:
            self.setToolTip("Stoerflaeche im Bild anklicken, um sie zu entfernen")
        elif not self._manual_circle_enabled:
            self.setToolTip(
                "Mausrad: zoomen | Ziehen: Ausschnitt verschieben | Doppelklick: anpassen"
            )

    def set_addition_mode_enabled(self, enabled: bool) -> None:
        self._addition_mode_enabled = enabled
        self._drag_start = None
        self._pending_circle_center = None
        self.setDragMode(
            QGraphicsView.NoDrag
            if enabled or self._manual_circle_enabled or self._exclusion_mode_enabled
            else QGraphicsView.ScrollHandDrag
        )
        if enabled:
            self.setToolTip(
                "Fehlende Blattflaeche anklicken, um sie als kleine Korrektur hinzuzufuegen"
            )
        elif not self._manual_circle_enabled and not self._exclusion_mode_enabled:
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
        if (
            self._exclusion_mode_enabled or self._addition_mode_enabled
        ) and self._pixmap:
            return
        if self._manual_circle_enabled and self._pixmap:
            self._drag_start = self.mapToScene(event.position().toPoint())
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
        if self._exclusion_mode_enabled and self._pixmap:
            point = self.mapToScene(event.position().toPoint())
            self.point_selected.emit((int(point.x()), int(point.y())))
            return
        if self._addition_mode_enabled and self._pixmap:
            point = self.mapToScene(event.position().toPoint())
            self.add_point_selected.emit((int(point.x()), int(point.y())))
            return
        if self._manual_circle_enabled and self._drag_start is not None:
            current = self.mapToScene(event.position().toPoint())
            dragged_radius = int(round(distance_between(self._drag_start, current)))
            if dragged_radius <= 3:
                if self._pending_circle_center is None:
                    self._pending_circle_center = current
                    self.set_petri_circle((int(current.x()), int(current.y()), 2), True)
                    self._drag_start = None
                    return

                radius = max(
                    1,
                    int(round(distance_between(self._pending_circle_center, current))),
                )
                circle = (
                    int(self._pending_circle_center.x()),
                    int(self._pending_circle_center.y()),
                    radius,
                )
                self._pending_circle_center = None
            else:
                circle = (
                    int(self._drag_start.x()),
                    int(self._drag_start.y()),
                    max(1, dragged_radius),
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
        self._inner_circle_item = None
        self._exclusion_items = []
        self._addition_items = []
        self._zoom_factor = 1.0
        self._scene.addText(self._placeholder_text)

    def _remove_circle(self) -> None:
        if self._circle_item is not None:
            self._scene.removeItem(self._circle_item)
            self._circle_item = None

    def _remove_inner_circle(self) -> None:
        if self._inner_circle_item is not None:
            self._scene.removeItem(self._inner_circle_item)
            self._inner_circle_item = None

    def _clear_exclusion_points(self) -> None:
        for item in self._exclusion_items:
            self._scene.removeItem(item)
        self._exclusion_items = []

    def _clear_addition_points(self) -> None:
        for item in self._addition_items:
            self._scene.removeItem(item)
        self._addition_items = []


def distance_between(first: QPointF, second: QPointF) -> float:
    delta_x = first.x() - second.x()
    delta_y = first.y() - second.y()
    return (delta_x * delta_x + delta_y * delta_y) ** 0.5
