# Scuteboard

Scuteboard is an alpha desktop board and match runner for Scrabble-like crossword games.

It is built with PySide6/Qt Widgets and speaks [CGP - Crossword Game Protocol](https://github.com/ArchooD2/CGP), a small stdin/stdout protocol for word-game engines. The current goal is to become a Cute Chess-like tool for crossword-game bots: launch engines, show the board, run bot-vs-bot matches, and keep enough logs to debug protocol behavior.

## Status

Scuteboard is early alpha software.

What works now:

- Qt desktop app with a 15x15 board
- Rack display and tile placement
- Move list and protocol log
- CGP bot process support
- One-bot auto-reply mode
- Bot-vs-bot mode with one CGP process per player
- Per-engine private `rack` and `unseen` state
- Stop after six consecutive passes or a max-ply limit

Still rough:

- Scoring is not complete
- Cross-word and dictionary validation are incomplete
- Engine configuration is basic
- Windows release packaging is experimental
- Tests are still needed

## Install

Use Python 3.11+ if possible.

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Build A Windows Release

This repo includes a GitHub Actions workflow that builds Scuteboard with PyInstaller on Windows.

To make a release build, push a version tag:

```bash
git tag v0.1.0-alpha.1
git push origin v0.1.0-alpha.1
```

The workflow uploads `Scuteboard-windows-x64.zip` as a workflow artifact and, for tag builds, attaches it to a GitHub release.

You can also run the workflow manually from GitHub Actions with `workflow_dispatch`.

## Run A CGP Bot

Open the `CGP Bot` dock in Scuteboard.

For a simple pass-only bot, use the reference engine from the CGP repo:

```text
python CGP/reference/PassTurtle.py
```

Click `Start`, then `Go`.

Scuteboard will send commands like:

```text
cgp
setup variant standard lexicon NWL23
ready
position 15/15/15/15/15/15/15/15/15/15/15/15/15/15/15
rack CTAESR?
unseen 5A2B1C3D8E1?
go movetime 1000
```

A conforming engine should answer:

```text
bestmove H8 SLATE
```

or:

```text
bestmove pass
```

During the alpha period, Scuteboard also tolerates direct move lines such as `pass`, but CGP engines should prefer the `bestmove` prefix.

## Bot-Vs-Bot

In the `CGP Bot` dock:

1. Enter a Player 1 command.
2. Enter a Player 2 command.
3. Check `Bot v bot`.
4. Click `Match`.

Scuteboard starts one process per engine. Only the active player's engine receives `go`.

Example shape:

```text
P1> position ...
P1> rack ...
P1> unseen ...
P1> go movetime 1000
P1< bestmove H8 LAD

P2> position ...
P2> rack ...
P2> unseen ...
P2> go movetime 1000
P2< bestmove pass
```

## CGP

CGP is the engine protocol used by Scuteboard.

- Spec repo: <https://github.com/ArchooD2/CGP>
- Current target: CGP draft `0.2`
- Transport: line-based stdin/stdout
- Server model: Scuteboard owns game state and validates engine moves
- Static resources: lexicons and tile sets are negotiated by name/hash, not sent every move

## Project Layout

```text
cgp/       CGP notation helpers
engine/    CGP engine process wrapper
model/     board, rack, tile, and turn state
ui/        PySide6 widgets and main window
input/     UI action dataclasses from the earlier prototype
assets/    placeholder package for future assets
```

## Good First Contributions

Useful small tasks:

- Add a screenshot to this README
- Add a random-move CGP bot
- Add tests for CGP move parsing
- Add tests for board import/export
- Improve bot move rejection messages
- Add `bestmove exchange` support
- Add a GitHub Actions compile check
- Add score calculation
- Add save/load for CGP positions

## Development Notes

Scuteboard is intentionally keeping the GUI/match runner authoritative. Engines suggest moves; Scuteboard validates and applies them.

That matters more for Scrabble-like games than for chess because move legality depends on shared static resources such as dictionaries and tile sets. CGP should identify those resources during setup, while Scuteboard remains the arbiter during a game.

## License

Scuteboard is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE).
