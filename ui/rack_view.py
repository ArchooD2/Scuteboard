from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class RackView(QWidget):
    tileSelected = Signal(int)
    SLOT_COUNT = 7

    def __init__(self) -> None:
        super().__init__()
        self.rack = []
        self.selected_tile_id: int | None = None
        self.slot_rects: list[QRect] = []
        self.setMinimumHeight(118)

    def set_rack(self, rack: list, selected_tile_id: int | None) -> None:
        self.rack = rack
        self.selected_tile_id = selected_tile_id
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(760, 128)

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.LeftButton:
            return

        for index, rect in enumerate(self.slot_rects):
            if index < len(self.rack) and rect.contains(event.position().toPoint()):
                self.tileSelected.emit(self.rack[index].id)
                return

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#2c3038"))

        margin = 16
        gap = 10
        usable = self.rect().adjusted(margin, 14, -margin, -14)
        slot_width = min(84, (usable.width() - gap * (self.SLOT_COUNT - 1)) // self.SLOT_COUNT)
        total_width = slot_width * self.SLOT_COUNT + gap * (self.SLOT_COUNT - 1)
        start_x = usable.x() + (usable.width() - total_width) // 2
        slot_height = usable.height()

        self.slot_rects = []
        for index in range(self.SLOT_COUNT):
            rect = QRect(start_x + index * (slot_width + gap), usable.y(), slot_width, slot_height)
            self.slot_rects.append(rect)
            painter.setPen(QPen(QColor("#737d8f"), 1))
            painter.setBrush(QColor("#3a404b"))
            painter.drawRoundedRect(rect, 5, 5)

            if index < len(self.rack):
                self._draw_tile(painter, rect.adjusted(7, 7, -7, -7), self.rack[index])

    def _draw_tile(self, painter: QPainter, rect: QRect, tile) -> None:
        is_selected = tile.id == self.selected_tile_id
        painter.setPen(QPen(QColor("#f0b943" if is_selected else "#6e604d"), 3 if is_selected else 2))
        painter.setBrush(QColor("#efe1bd"))
        painter.drawRoundedRect(rect, 6, 6)

        painter.setPen(QColor("#28221a"))
        painter.setFont(QFont("Segoe UI", 26, QFont.Bold))
        painter.drawText(rect, Qt.AlignCenter, tile.letter)

        painter.setPen(QColor("#6e604d"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(rect.adjusted(0, 0, -8, -5), Qt.AlignRight | Qt.AlignBottom, str(tile.value))
