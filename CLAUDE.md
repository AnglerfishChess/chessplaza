# chessplaza

AI chess hustlers with distinct personalities. Like NYC Washington Square Park, but in your terminal.

## Stack
- `claude-agent-sdk` - agent framework (query Context7 for docs)
- `chess-uci-mcp` - UCI engine interface via MCP
- `esca` - board representation and move validation

## Architecture
Each hustler = Claude agent with personality prompt + access to chess engine via MCP.

## MCP Tools
- **Context7** - library docs lookup (use instead of guessing APIs)
- **Serena** - semantic code navigation (prefer over grep/read for code exploration)

## Style
- No local imports (imports inside functions) unless truly necessary
- Type hints encouraged; write optionals as `T | None` (ruff's `UP` rules enforce it)

## Tests

Structure:
- `tests/proto/` - experimental prototypes and spike tests
- `tests/unit/` - unit tests (pytest), paths mirror source: `chessplaza/foo/bar.py` → `tests/unit/foo/test_bar.py`

## Before Committing Milestones

Run the full gate:
```bash
uvx ruff check --fix . && uvx ruff format .
uvx pyrefly check
uv run --no-sync pytest
```

`pytest` excludes the `llm`-marked tests by default; they need a live Claude
session. Run them with `uv run --no-sync pytest -m llm`.

## Output Architecture
- **Critical errors** → `logger.error`/`logger.critical` → always to stderr (console)
- **Gameplay output** → `rich` Console → configurable target (console or GUI widget)
- **Debug/info logs** → `logger.debug`/`logger.info` → enabled via `--log`/`--debug` flags

The logging module handles errors/diagnostics (always available), while rich handles
user-facing gameplay text (can be redirected to different UI backends).
