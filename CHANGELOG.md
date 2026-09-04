# Changelog

## 0.1.0 (2026-09-04)

- Chess hustlers with distinct personalities, driven by the Claude Agent SDK:
  a park scene to pick an opponent from, and a dialog loop with the one chosen.
- Board state, move validation, game status and ECO opening names come from
  the in-house `esca` library, served to the agent as an in-process MCP server
  (`new_game`, `make_move`, `get_position`, `get_legal_moves`).
- UCI engines are reached through `chess-uci-mcp`, launched by `uvx`.
- Optional text-to-speech (`voice` extra) and a PySide6 UI prototype
  (`gui` extra).
