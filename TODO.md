# Scuteboard TODO

Scuteboard now uses PySide6/Qt Widgets instead of Pygame. The current target is a Scrabble board tool with a desktop layout closer to Cute Chess: native menus, toolbar actions, dockable panels, a central board, rack panel, move list, and log.

## Done

- Replace the Pygame event loop with a Qt application entry point in `main.py`.
- Add a Qt `QMainWindow` shell in `ui/main_window.py`.
- Add a custom painted Qt board widget in `ui/board_view.py`.
- Add a custom painted Qt rack widget in `ui/rack_view.py`.
- Update `requirements.txt` to depend on `PySide6`.
- Remove the obsolete Pygame UI modules.
- Add initial CGP bot process support with `cgp`, `setup`, `ready`, `position`, `rack`, `unseen`, `go`, `bestmove`, direct moves, and pass handling.
- Add a two-engine bot-vs-bot runner with per-player commands, active-player engine routing, max-ply stop, and consecutive-pass stop.

## Next

- Add proper scoring and cross-word validation.
- Add save/load for CGP positions.
- Add engine/player configuration panels like Cute Chess.
- Add clocks or per-player timersfor timed matches.
- Add tests for board validation, CGP import/export, and turn submission.

## Run

```bash
python -m pip install -r requirements.txt
python main.py
```
