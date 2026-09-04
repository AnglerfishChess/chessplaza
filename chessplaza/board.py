"""Chess board state management via in-process MCP server."""

import json
from typing import Any

import esca
from claude_agent_sdk import create_sdk_mcp_server, tool


def _new_game(fen: str | None = None) -> esca.Game:
    """A game from `fen`, or from the starting position.

    Castling is written `e1g1`, the form UCI engines speak.
    """
    game = esca.Game() if fen is None else esca.Game.from_fen(fen)
    game.castling_output = esca.KING_TWO_SQUARES
    return game


# Global game state (one game at a time)
_game: esca.Game = _new_game()


def _reply(payload: dict[str, Any]) -> dict[str, Any]:
    """Wrap a payload as the JSON text content of an MCP tool result."""
    return {"content": [{"type": "text", "text": json.dumps(payload)}]}


def _game_status() -> str:
    """Current game status: `checkmate`, `stalemate`, `draw` or `ongoing`.

    A draw a player may still claim (threefold repetition, fifty moves) counts
    as a draw.
    """
    outcome = _game.outcome()
    if outcome in ("checkmate", "stalemate"):
        return outcome
    if outcome is not None or _game.claims():
        return "draw"
    return "ongoing"


def _turn() -> str:
    """Side to move, as `white` or `black`."""
    return "white" if _game.position.side_to_move == "w" else "black"


def _opening_name() -> str | None:
    """The ECO name of the deepest opening the game reached, if any."""
    opening = _game.opening()
    return opening.name if opening is not None else None


def _resolve(text: str) -> tuple[esca.Move | None, str]:
    """The legal move `text` names, in SAN or UCI, and why it is not one.

    Exactly one of the pair is meaningful: a move and an empty reason, or
    `None` and a reason naming what each notation made of the text.
    """
    reasons: list[str] = []
    for play in (esca.Game.play_san, esca.Game.play):
        probe = esca.Game.from_position(_game.position)
        try:
            play(probe, text)
        except ValueError as exc:
            reasons.append(str(exc))
        else:
            return probe.moves[-1], ""
    return None, " / ".join(dict.fromkeys(reasons))


@tool("new_game", "Start a new chess game. Resets the board to starting position.", {})
async def new_game(args: dict[str, Any]) -> dict[str, Any]:
    """Reset the board to starting position."""
    global _game
    _game = _new_game()
    return _reply(
        {
            "fen": _game.position.fen,
            "game_status": "ongoing",
            "turn": "white",
            "opening": _opening_name(),
        }
    )


@tool("make_move", "Make a chess move. Accepts SAN (Nf3, e4, O-O) or UCI (g1f3, e2e4).", {"move": str})
async def make_move(args: dict[str, Any]) -> dict[str, Any]:
    """Apply a move to the board."""
    move_input = args.get("move", "").strip()

    move, reason = _resolve(move_input)
    if move is None:
        return _reply(
            {
                "valid": False,
                "error": f"{reason}: {move_input}",
                "fen": _game.position.fen,
                "game_status": _game_status(),
            }
        )

    # Notation is taken before the move is played: SAN reads against the position it is played in.
    san = _game.move_to_san(move)
    uci = _game.move_to_uci(move)

    _game.play(move)

    return _reply(
        {
            "valid": True,
            "san": san,
            "uci": uci,
            "fen": _game.position.fen,
            "game_status": _game_status(),
            "turn": _turn(),
            "opening": _opening_name(),
        }
    )


@tool("get_position", "Get the current board position as FEN.", {})
async def get_position(args: dict[str, Any]) -> dict[str, Any]:
    """Return current board state."""
    return _reply(
        {
            "fen": _game.position.fen,
            "game_status": _game_status(),
            "turn": _turn(),
            "opening": _opening_name(),
        }
    )


@tool("get_legal_moves", "Get all legal moves in the current position.", {})
async def get_legal_moves(args: dict[str, Any]) -> dict[str, Any]:
    """List all legal moves."""
    moves = [_game.move_to_san(m) for m in _game.legal_moves()]
    return _reply(
        {
            "legal_moves": moves,
            "count": len(moves),
        }
    )


def create_board_mcp_server():
    """Create the chessplaza board MCP server."""
    return create_sdk_mcp_server(
        name="plaza", version="1.0.0", tools=[new_game, make_move, get_position, get_legal_moves]
    )
