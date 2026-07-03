from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QDockWidget,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStatusBar,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from engine.cgp_engine import CgpEngine
from model.game_state import GameState
from .board_view import BoardView
from .rack_view import RackView


class MainWindow(QMainWindow):
    def __init__(self, state: GameState) -> None:
        super().__init__()
        self.state = state
        self.selected_tile_id: int | None = None
        self.last_error: str | None = None

        self.setWindowTitle("Scuteboard")
        self.resize(1180, 900)

        self.board_view = BoardView()
        self.rack_view = RackView()
        self.move_list = QListWidget()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.engines = [CgpEngine(self), CgpEngine(self)]
        self.engine = self.engines[0]
        self.engine_ready = [False, False]
        self.waiting_engine_index: int | None = None
        self.bot_match_running = False
        self.bot_match_plies = 0
        self.consecutive_passes = 0
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self._build_actions()
        self._build_menus()
        self._build_toolbar()
        self._build_central_area()
        self._build_docks()
        self._connect_signals()
        self.refresh()
        self._log("New game ready.")

    def _build_actions(self) -> None:
        self.new_game_action = QAction("New Game", self)
        self.new_game_action.setShortcut(QKeySequence.New)

        self.submit_action = QAction("Submit Move", self)
        self.submit_action.setShortcut(QKeySequence(Qt.Key_Return))

        self.pass_action = QAction("Pass", self)
        self.swap_action = QAction("Swap", self)

        self.flip_action = QAction("Flip Board", self)
        self.flip_action.setCheckable(True)

        self.coords_action = QAction("Coordinates", self)
        self.coords_action.setCheckable(True)
        self.coords_action.setChecked(True)

        self.recall_action = QAction("Recall Tiles", self)
        self.recall_action.setShortcut(QKeySequence("Ctrl+R"))

    def _build_menus(self) -> None:
        game_menu = self.menuBar().addMenu("&Game")
        game_menu.addAction(self.new_game_action)
        game_menu.addSeparator()
        game_menu.addAction(self.submit_action)
        game_menu.addAction(self.pass_action)
        game_menu.addAction(self.swap_action)
        game_menu.addAction(self.recall_action)

        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self.flip_action)
        view_menu.addAction(self.coords_action)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Game", self)
        toolbar.setMovable(False)
        toolbar.addAction(self.new_game_action)
        toolbar.addSeparator()
        toolbar.addAction(self.submit_action)
        toolbar.addAction(self.pass_action)
        toolbar.addAction(self.swap_action)
        toolbar.addSeparator()
        toolbar.addAction(self.recall_action)
        toolbar.addAction(self.flip_action)
        self.addToolBar(toolbar)

    def _build_central_area(self) -> None:
        shell = QWidget()
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)
        layout.addWidget(self.board_view, 1, Qt.AlignCenter)
        self.setCentralWidget(shell)

    def _build_docks(self) -> None:
        self.addDockWidget(Qt.BottomDockWidgetArea, self._rack_dock())
        self.addDockWidget(Qt.RightDockWidgetArea, self._game_dock())
        self.addDockWidget(Qt.RightDockWidgetArea, self._engine_dock())
        self.addDockWidget(Qt.RightDockWidgetArea, self._moves_dock())
        self.addDockWidget(Qt.RightDockWidgetArea, self._log_dock())

    def _rack_dock(self) -> QDockWidget:
        dock = QDockWidget("Rack", self)
        dock.setObjectName("rackDock")
        dock.setWidget(self.rack_view)
        return dock

    def _game_dock(self) -> QDockWidget:
        dock = QDockWidget("Game", self)
        dock.setObjectName("gameDock")

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.player_label = QLabel()
        self.score_label = QLabel()
        self.bag_label = QLabel()
        self.error_label = QLabel()
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)

        buttons = QFrame()
        button_layout = QHBoxLayout(buttons)
        button_layout.setContentsMargins(0, 4, 0, 0)
        for text, slot in (
            ("Submit", self.submit_move),
            ("Pass", self.pass_turn),
            ("Swap", self.swap_tiles),
        ):
            button = QPushButton(text)
            button.clicked.connect(slot)
            button_layout.addWidget(button)

        layout.addWidget(self.player_label)
        layout.addWidget(self.score_label)
        layout.addWidget(self.bag_label)
        layout.addWidget(self.error_label)
        layout.addWidget(buttons)
        layout.addStretch(1)

        dock.setWidget(panel)
        return dock

    def _engine_dock(self) -> QDockWidget:
        dock = QDockWidget("CGP Bot", self)
        dock.setObjectName("engineDock")

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        form = QFormLayout()
        self.engine_command = QLineEdit()
        self.engine_command.setPlaceholderText("python path/to/player1_bot.py")
        self.engine_2_command = QLineEdit()
        self.engine_2_command.setPlaceholderText("python path/to/player2_bot.py")
        self.engine_movetime = QSpinBox()
        self.engine_movetime.setRange(50, 600000)
        self.engine_movetime.setValue(1000)
        self.engine_movetime.setSuffix(" ms")
        self.engine_max_plies = QSpinBox()
        self.engine_max_plies.setRange(1, 1000)
        self.engine_max_plies.setValue(200)
        self.engine_max_plies.setSuffix(" plies")
        self.engine_auto_reply = QCheckBox("Auto reply")
        self.engine_auto_reply.setChecked(True)
        self.engine_bot_v_bot = QCheckBox("Bot v bot")
        form.addRow("Player 1", self.engine_command)
        form.addRow("Player 2", self.engine_2_command)
        form.addRow("Move time", self.engine_movetime)
        form.addRow("Max", self.engine_max_plies)
        form.addRow("", self.engine_auto_reply)
        form.addRow("", self.engine_bot_v_bot)

        self.engine_status = QLabel("Stopped")
        self.engine_status.setWordWrap(True)

        buttons = QFrame()
        button_layout = QHBoxLayout(buttons)
        button_layout.setContentsMargins(0, 4, 0, 0)
        self.start_engine_button = QPushButton("Start")
        self.stop_engine_button = QPushButton("Stop")
        self.bot_move_button = QPushButton("Go")
        self.bot_match_button = QPushButton("Match")
        self.start_engine_button.clicked.connect(self.start_engine)
        self.stop_engine_button.clicked.connect(self.stop_engine)
        self.bot_move_button.clicked.connect(self.request_bot_move)
        self.bot_match_button.clicked.connect(self.start_bot_match)
        button_layout.addWidget(self.start_engine_button)
        button_layout.addWidget(self.stop_engine_button)
        button_layout.addWidget(self.bot_move_button)
        button_layout.addWidget(self.bot_match_button)

        layout.addLayout(form)
        layout.addWidget(self.engine_status)
        layout.addWidget(buttons)
        layout.addStretch(1)

        dock.setWidget(panel)
        return dock

    def _moves_dock(self) -> QDockWidget:
        dock = QDockWidget("Moves", self)
        dock.setObjectName("movesDock")
        dock.setWidget(self.move_list)
        return dock

    def _log_dock(self) -> QDockWidget:
        dock = QDockWidget("Log", self)
        dock.setObjectName("logDock")
        self.log.setMinimumWidth(260)
        self.log.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        dock.setWidget(self.log)
        return dock

    def _connect_signals(self) -> None:
        self.new_game_action.triggered.connect(self.new_game)
        self.submit_action.triggered.connect(self.submit_move)
        self.pass_action.triggered.connect(self.pass_turn)
        self.swap_action.triggered.connect(self.swap_tiles)
        self.recall_action.triggered.connect(self.recall_tiles)
        self.flip_action.toggled.connect(self.set_board_flipped)
        self.coords_action.toggled.connect(self.set_coordinates_visible)
        self.rack_view.tileSelected.connect(self.select_tile)
        self.board_view.cellClicked.connect(self.place_selected_tile)
        for index, engine in enumerate(self.engines):
            engine.lineSent.connect(lambda line, engine_index=index: self._log(f"P{engine_index + 1}> {line}"))
            engine.lineReceived.connect(lambda line, engine_index=index: self.handle_engine_line(engine_index, line))
            engine.errorReceived.connect(lambda message, engine_index=index: self.handle_engine_error(engine_index, message))
            engine.bestMoveReceived.connect(lambda bestmove, engine_index=index: self.apply_bot_move(engine_index, bestmove))
            engine.stateChanged.connect(lambda state, engine_index=index: self.handle_engine_state(engine_index, state))

    def refresh(self) -> None:
        self.board_view.set_board(self.state.board)
        self.rack_view.set_rack(self.state.rack, self.selected_tile_id)

        self.player_label.setText(f"Turn: {self.state.current_player_name()}")
        self.score_label.setText(
            f"Score: {self.state.player_1_score} - {self.state.player_2_score}"
        )
        self.bag_label.setText(f"Bag: {len(self.state.bag)} tiles")
        self.error_label.setText(f"Last result: {self.last_error}" if self.last_error else "")

        selected = self.state.rack_tile_by_id(self.selected_tile_id) if self.selected_tile_id is not None else None
        selected_text = f" | selected {selected.letter}" if selected is not None else ""
        self.status.showMessage(
            f"{self.state.current_player_name()} | rack {len(self.state.rack)} | bag {len(self.state.bag)}{selected_text}"
        )
        if hasattr(self, "bot_move_button"):
            any_running = any(engine.is_running() for engine in self.engines)
            self.bot_move_button.setEnabled(self._active_engine().is_running())
            self.stop_engine_button.setEnabled(any_running)
            self.bot_match_button.setEnabled(any_running and not self.bot_match_running)

    def select_tile(self, tile_id: int) -> None:
        self.selected_tile_id = None if self.selected_tile_id == tile_id else tile_id
        self.last_error = None
        self.refresh()

    def place_selected_tile(self, row: int, column: int) -> None:
        if self.selected_tile_id is None:
            return

        tile = self.state.rack_tile_by_id(self.selected_tile_id)
        placed = self.state.stage_tile(self.selected_tile_id, row, column)
        if placed:
            self.last_error = None
            if tile is not None:
                self._log(f"Staged {tile.letter} at {self._square_name(row, column)}.")
            self.selected_tile_id = None
        else:
            self.last_error = "cannot_place_here"
        self.refresh()

    def submit_move(self) -> None:
        pending = self.state.board.pending_tiles()
        error = self.state.submit_turn()
        self.last_error = error
        if error is None:
            move_text = self._describe_pending(pending)
            self.move_list.addItem(move_text)
            self.selected_tile_id = None
            self._log(f"Submitted {move_text}.")
            self.request_auto_bot_move()
        else:
            self._log(f"Move rejected: {error}.")
        self.refresh()

    def pass_turn(self) -> None:
        self.state.pass_turn()
        self.selected_tile_id = None
        self.last_error = None
        self.move_list.addItem(f"{self.state.turn_number}. pass")
        self._log("Turn passed.")
        self.refresh()
        self.request_auto_bot_move()

    def swap_tiles(self) -> None:
        swapped = self.state.swap_turn()
        self.selected_tile_id = None
        self.last_error = None if swapped else "swap_unavailable"
        self.move_list.addItem(f"{self.state.turn_number}. swap" if swapped else "swap failed")
        self._log("Tiles swapped." if swapped else "Swap unavailable.")
        self.refresh()
        if swapped:
            self.request_auto_bot_move()

    def recall_tiles(self) -> None:
        self.state.recall_pending_tiles()
        self.selected_tile_id = None
        self.last_error = None
        self._log("Pending tiles recalled.")
        self.refresh()

    def new_game(self) -> None:
        self.state.reset()
        self.selected_tile_id = None
        self.last_error = None
        self.bot_match_plies = 0
        self.consecutive_passes = 0
        self.move_list.clear()
        self._log("New game started.")
        self.refresh()

    def start_engine(self) -> None:
        self.engine_ready = [False, False]
        self.engines[0].start(self.engine_command.text())
        if self.engine_bot_v_bot.isChecked() or self.engine_2_command.text().strip():
            self.engines[1].start(self.engine_2_command.text())

    def stop_engine(self) -> None:
        self.bot_match_running = False
        self.waiting_engine_index = None
        for engine in self.engines:
            engine.stop()
        self.refresh()

    def request_bot_move(self) -> None:
        if self.waiting_engine_index is not None:
            return

        self.state.recall_pending_tiles()
        self.selected_tile_id = None
        self.last_error = None
        self.refresh()
        engine_index = self._active_engine_index()
        engine = self.engines[engine_index]
        if not engine.is_running():
            self.handle_engine_error(engine_index, "engine_not_running")
            return
        self.waiting_engine_index = engine_index
        engine.request_move(self.state, self.engine_movetime.value())

    def apply_bot_move(self, engine_index: int, bestmove: str) -> None:
        if self.waiting_engine_index is not None and engine_index != self.waiting_engine_index:
            self._log(f"Ignored P{engine_index + 1} move while waiting for P{self.waiting_engine_index + 1}.")
            return

        self.waiting_engine_index = None
        before_turn = self.state.turn_number
        error = self.state.play_cgp_bestmove(bestmove)
        self.last_error = error
        if error is None:
            move_number = self.state.turn_number
            self.bot_match_plies += 1
            if bestmove.strip().lower() == "pass":
                self.consecutive_passes += 1
            else:
                self.consecutive_passes = 0
            self.move_list.addItem(f"{move_number}. P{engine_index + 1} {bestmove}")
            self._log(f"P{engine_index + 1} played {bestmove}.")
        else:
            self.bot_match_running = False
            self._log(f"P{engine_index + 1} move rejected: {error}.")

        if self.state.turn_number == before_turn and error is None:
            self._log("Bot move did not advance the turn.")
        self.refresh()
        self.continue_bot_match()

    def request_auto_bot_move(self) -> None:
        if self.engine_auto_reply.isChecked() and self._active_engine().is_running():
            self.request_bot_move()

    def handle_engine_line(self, engine_index: int, line: str) -> None:
        self._log(f"P{engine_index + 1}< {line}")
        if line == "readyok":
            self.engine_ready[engine_index] = True
            if self.bot_match_running:
                self.continue_bot_match()
            else:
                self.request_auto_bot_move()

    def handle_engine_error(self, engine_index: int, message: str) -> None:
        self.waiting_engine_index = None
        self.bot_match_running = False
        self.engine_status.setText(f"P{engine_index + 1} error: {message}")
        self._log(f"P{engine_index + 1}! {message}")

    def handle_engine_state(self, engine_index: int, state: str) -> None:
        self.engine_status.setText(self._engine_status_text())
        self._log(f"P{engine_index + 1} engine {state}.")
        if state == "started":
            self.engines[engine_index].handshake()
        elif state.startswith("stopped"):
            self.engine_ready[engine_index] = False
            self.bot_match_running = False
        self.refresh()

    def start_bot_match(self) -> None:
        self.bot_match_running = True
        self.engine_bot_v_bot.setChecked(True)
        if not all(engine.is_running() for engine in self.engines):
            self.start_engine()
            return
        self.continue_bot_match()

    def continue_bot_match(self) -> None:
        if not self.bot_match_running:
            return

        if not all(self.engine_ready):
            return

        if self.waiting_engine_index is not None:
            return

        if self.bot_match_plies >= self.engine_max_plies.value():
            self.bot_match_running = False
            self._log("Bot match stopped: max plies reached.")
            self.refresh()
            return

        if self.consecutive_passes >= 6:
            self.bot_match_running = False
            self._log("Bot match stopped: six consecutive passes.")
            self.refresh()
            return

        self.request_bot_move()

    def _active_engine_index(self) -> int:
        if self.engine_bot_v_bot.isChecked():
            return self.state.active_player_index
        return 0

    def _active_engine(self) -> CgpEngine:
        return self.engines[self._active_engine_index()]

    def _engine_status_text(self) -> str:
        labels = []
        for index, engine in enumerate(self.engines):
            state = "running" if engine.is_running() else "stopped"
            ready = "ready" if self.engine_ready[index] else "not ready"
            labels.append(f"P{index + 1}: {state}, {ready}")
        return " | ".join(labels)

    def set_board_flipped(self, flipped: bool) -> None:
        self.board_view.set_flipped(flipped)
        self.refresh()

    def set_coordinates_visible(self, visible: bool) -> None:
        self.board_view.set_coordinates_visible(visible)
        self.refresh()

    def _describe_pending(self, pending) -> str:
        if not pending:
            return f"{self.state.turn_number}. move"

        rows = {placed.row for placed in pending}
        columns = {placed.column for placed in pending}
        if len(rows) == 1 and len(columns) > 1:
            start_row, start_column, letters = self._word_span(next(iter(rows)), min(columns), 0, 1)
        elif len(columns) == 1 and len(rows) > 1:
            start_row, start_column, letters = self._word_span(min(rows), next(iter(columns)), 1, 0)
        else:
            placed = pending[0]
            horizontal = self._word_span(placed.row, placed.column, 0, 1)
            vertical = self._word_span(placed.row, placed.column, 1, 0)
            start_row, start_column, letters = horizontal if len(horizontal[2]) >= len(vertical[2]) else vertical

        return f"{self.state.turn_number}. {letters} @ {self._square_name(start_row, start_column)}"

    def _word_span(self, row: int, column: int, step_row: int, step_column: int) -> tuple[int, int, str]:
        start_row = row
        start_column = column
        while True:
            previous_row = start_row - step_row
            previous_column = start_column - step_column
            if self.state.board.tile_at(previous_row, previous_column) is None:
                break
            start_row = previous_row
            start_column = previous_column

        letters: list[str] = []
        current_row = start_row
        current_column = start_column
        while True:
            placed_tile = self.state.board.tile_at(current_row, current_column)
            if placed_tile is None:
                break
            letters.append(placed_tile.tile.letter)
            current_row += step_row
            current_column += step_column

        return start_row, start_column, "".join(letters)

    def _square_name(self, row: int, column: int) -> str:
        return f"{chr(ord('A') + column)}{row + 1}"

    def _log(self, message: str) -> None:
        self.log.append(message)
