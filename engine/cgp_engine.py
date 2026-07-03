from __future__ import annotations

from PySide6.QtCore import QObject, QProcess, Signal

from cgp.protocol import format_tile_counts, parse_cgp_move
from model.game_state import GameState


class CgpEngine(QObject):
    lineReceived = Signal(str)
    lineSent = Signal(str)
    bestMoveReceived = Signal(str)
    errorReceived = Signal(str)
    stateChanged = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._read_stdout)
        self.process.readyReadStandardError.connect(self._read_stderr)
        self.process.started.connect(lambda: self.stateChanged.emit("started"))
        self.process.finished.connect(lambda exit_code, exit_status: self.stateChanged.emit(f"stopped {exit_code}"))
        self._buffer = ""
        self._stderr_buffer = ""

    def is_running(self) -> bool:
        return self.process.state() != QProcess.NotRunning

    def start(self, command: str) -> None:
        if self.is_running():
            return

        if not command.strip():
            self.errorReceived.emit("missing_engine_command")
            return

        self.process.startCommand(command)

    def stop(self) -> None:
        if not self.is_running():
            return

        self.send("quit")
        self.process.closeWriteChannel()
        if not self.process.waitForFinished(1000):
            self.process.kill()

    def handshake(self) -> None:
        self.send("cgp")
        self.send("setup variant standard lexicon NWL23")
        self.send("ready")

    def request_move(self, state: GameState, movetime_ms: int) -> None:
        if not self.is_running():
            self.errorReceived.emit("engine_not_running")
            return

        self.send(f"position {state.cgp_board()}")
        self.send(f"rack {state.cgp_rack()}")
        unseen = state.bag + (state.player_2_rack if state.active_player_index == 0 else state.player_1_rack)
        if unseen:
            self.send(f"unseen {format_tile_counts(unseen)}")
        self.send(f"go movetime {movetime_ms}")

    def send(self, line: str) -> None:
        if not self.is_running():
            return

        self.process.write(f"{line}\n".encode("utf-8"))
        self.lineSent.emit(line)

    def _read_stdout(self) -> None:
        self._buffer += bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self._handle_line(line.strip())

    def _read_stderr(self) -> None:
        self._stderr_buffer += bytes(self.process.readAllStandardError()).decode("utf-8", errors="replace")
        while "\n" in self._stderr_buffer:
            line, self._stderr_buffer = self._stderr_buffer.split("\n", 1)
            line = line.strip()
            if line:
                self.errorReceived.emit(line)

    def _handle_line(self, line: str) -> None:
        if not line:
            return

        self.lineReceived.emit(line)
        if line.startswith("bestmove "):
            self.bestMoveReceived.emit(line.removeprefix("bestmove ").strip())
        elif line.startswith("error "):
            self.errorReceived.emit(line.removeprefix("error ").strip())
        elif self._looks_like_move(line):
            self.bestMoveReceived.emit(line)

    def _looks_like_move(self, line: str) -> bool:
        lowered = line.lower()
        if lowered == "pass" or lowered.startswith("exchange "):
            return True

        try:
            parse_cgp_move(line)
        except ValueError:
            return False
        return True
