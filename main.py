import sys

from PySide6.QtWidgets import QApplication

from model.game_state import GameState
from ui.main_window import MainWindow


class ScuteboardApp:
    def __init__(self) -> None:
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName("Scuteboard")
        self.state = GameState()
        self.window = MainWindow(self.state)

    def run(self) -> int:
        self.window.show()
        return self.qt_app.exec()


def main() -> int:
    app = ScuteboardApp()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
