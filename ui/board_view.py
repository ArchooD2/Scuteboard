from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class BoardView(QWidget):
    cellClicked = Signal(int, int)
    BOARD_SIZE = 15

    def __init__(self) -> None:
        super().__init__()
        self.board = None
        self.hover_cell: tuple[int, int] | None = None
        self.flipped = False
        self.show_coordinates = True
        self.setMouseTracking(True)
        self.setMinimumSize(QSize(520, 520))

    def set_board(self, board) -> None:
        self.board = board
        self.update()

    def set_flipped(self, flipped: bool) -> None:
        self.flipped = flipped
        self.update()

    def set_coordinates_visible(self, visible: bool) -> None:
        self.show_coordinates = visible
        self.update()

    def board_rect(self) -> QRect:
        margin = 34 if self.show_coordinates else 10
        available = self.rect().adjusted(margin, margin, -margin, -margin)
        side = min(available.width(), available.height())
        x = available.x() + (available.width() - side) // 2
        y = available.y() + (available.height() - side) // 2
        return QRect(x, y, side, side)

    def cell_rect(self, row: int, column: int) -> QRect:
        board_rect = self.board_rect()
        cell_size = board_rect.width() / self.BOARD_SIZE
        display_row = self.BOARD_SIZE - 1 - row if self.flipped else row
        display_column = self.BOARD_SIZE - 1 - column if self.flipped else column
        return QRect(
            round(board_rect.x() + display_column * cell_size),
            round(board_rect.y() + display_row * cell_size),
            round(cell_size + 0.5),
            round(cell_size + 0.5),
        )

    def point_to_cell(self, point: QPoint) -> tuple[int, int] | None:
        board_rect = self.board_rect()
        if not board_rect.contains(point):
            return None

        cell_size = board_rect.width() / self.BOARD_SIZE
        display_column = int((point.x() - board_rect.x()) / cell_size)
        display_row = int((point.y() - board_rect.y()) / cell_size)
        if not (0 <= display_row < self.BOARD_SIZE and 0 <= display_column < self.BOARD_SIZE):
            return None

        row = self.BOARD_SIZE - 1 - display_row if self.flipped else display_row
        column = self.BOARD_SIZE - 1 - display_column if self.flipped else display_column
        return row, column

    def mouseMoveEvent(self, event) -> None:
        self.hover_cell = self.point_to_cell(event.position().toPoint())
        self.update()

    def leaveEvent(self, event) -> None:
        self.hover_cell = None
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.LeftButton:
            return

        cell = self.point_to_cell(event.position().toPoint())
        if cell is not None:
            self.cellClicked.emit(cell[0], cell[1])

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#23272e"))

        board_rect = self.board_rect()
        painter.setPen(QPen(QColor("#3f372c"), 2))
        painter.setBrush(QColor("#f3ead5"))
        painter.drawRect(board_rect)

        for row in range(self.BOARD_SIZE):
            for column in range(self.BOARD_SIZE):
                rect = self.cell_rect(row, column)
                painter.fillRect(rect, self._cell_color(row, column))
                painter.setPen(QPen(QColor("#7b6d59"), 1))
                painter.drawRect(rect)

                if self.hover_cell == (row, column):
                    painter.setPen(QPen(QColor("#f0b943"), 3))
                    painter.drawRect(rect.adjusted(1, 1, -1, -1))

                self._draw_premium_label(painter, row, column, rect)
                self._draw_tile(painter, row, column, rect)

        if self.show_coordinates:
            self._draw_coordinates(painter)

    def _cell_color(self, row: int, column: int) -> QColor:
        premium = self.board.premium_at(row, column) if self.board is not None else None
        colors = {
            "TW": "#c65454",
            "DW": "#e69b9b",
            "TL": "#4a6dad",
            "DL": "#9bc5ef",
        }
        return QColor(colors.get(premium, "#f7efd9"))

    def _draw_premium_label(self, painter: QPainter, row: int, column: int, rect: QRect) -> None:
        if self.board is None:
            return

        premium = self.board.premium_at(row, column)
        if premium is None:
            return

        painter.setPen(QColor("#473d33"))
        font = QFont("Segoe UI", max(7, rect.height() // 6), QFont.Bold)
        painter.setFont(font)
        label = "*" if row == 7 and column == 7 else premium
        painter.drawText(rect, Qt.AlignCenter, label)

    def _draw_tile(self, painter: QPainter, row: int, column: int, rect: QRect) -> None:
        if self.board is None:
            return

        placed_tile = self.board.tile_at(row, column)
        if placed_tile is None:
            return

        tile_rect = rect.adjusted(5, 5, -5, -5)
        painter.setPen(QPen(QColor("#5f523f"), 2))
        painter.setBrush(QColor("#efe1bd"))
        painter.drawRoundedRect(tile_rect, 5, 5)

        letter_font = QFont("Segoe UI", max(14, tile_rect.height() // 2), QFont.Bold)
        painter.setFont(letter_font)
        painter.setPen(QColor("#28221a"))
        painter.drawText(tile_rect, Qt.AlignCenter, placed_tile.tile.letter)

        value_font = QFont("Segoe UI", max(7, tile_rect.height() // 6), QFont.Bold)
        painter.setFont(value_font)
        painter.setPen(QColor("#6e604d"))
        painter.drawText(tile_rect.adjusted(0, 0, -5, -3), Qt.AlignRight | Qt.AlignBottom, str(placed_tile.tile.value))

    def _draw_coordinates(self, painter: QPainter) -> None:
        font = QFont("Segoe UI", 10, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#d8dde6"))

        for row in range(self.BOARD_SIZE):
            label_value = self.BOARD_SIZE - row if self.flipped else row + 1
            rect = self.cell_rect(row, 0)
            painter.drawText(QRect(0, rect.y(), self.board_rect().left() - 8, rect.height()), Qt.AlignRight | Qt.AlignVCenter, str(label_value))

        for column in range(self.BOARD_SIZE):
            file_index = self.BOARD_SIZE - 1 - column if self.flipped else column
            label = chr(ord("A") + file_index)
            rect = self.cell_rect(0, column)
            painter.drawText(QRect(rect.x(), self.board_rect().bottom() + 6, rect.width(), 24), Qt.AlignCenter, label)
