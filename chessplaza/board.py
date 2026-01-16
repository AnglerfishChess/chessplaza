"""Chess board state management via in-process MCP server."""

import json
from typing import Any

import chess

from claude_agent_sdk import tool, create_sdk_mcp_server


# Global board state (one game at a time)
_board: chess.Board = chess.Board()


def _game_status() -> str:
    """Get current game status."""
    if _board.is_checkmate():
        return "checkmate"
    if _board.is_stalemate():
        return "stalemate"
    if _board.is_insufficient_material() or _board.is_fifty_moves() or _board.is_repetition():
        return "draw"
    return "ongoing"


@tool("new_game", "Start a new chess game. Resets the board to starting position.", {})
async def new_game(args: dict[str, Any]) -> dict[str, Any]:
    """Reset the board to starting position."""
    global _board
    _board = chess.Board()
    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "fen": _board.fen(),
                "game_status": "ongoing",
                "turn": "white",
            })
        }]
    }


@tool(
    "make_move",
    "Make a chess move. Accepts SAN (Nf3, e4, O-O) or UCI (g1f3, e2e4).",
    {"move": str}
)
async def make_move(args: dict[str, Any]) -> dict[str, Any]:
    """Apply a move to the board."""
    move_input = args.get("move", "").strip()

    # Try SAN first (e.g., "Nf3", "e4", "O-O")
    parsed = None
    try:
        parsed = _board.parse_san(move_input)
    except (chess.InvalidMoveError, chess.AmbiguousMoveError):
        pass

    # Try UCI (e.g., "e2e4", "g1f3")
    if parsed is None:
        try:
            parsed = _board.parse_uci(move_input)
        except (chess.InvalidMoveError, ValueError):
            pass

    if parsed is None:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "valid": False,
                    "error": f"Invalid notation: {move_input}",
                    "fen": _board.fen(),
                    "game_status": _game_status(),
                })
            }]
        }

    if parsed not in _board.legal_moves:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "valid": False,
                    "error": f"Illegal move: {move_input}",
                    "fen": _board.fen(),
                    "game_status": _game_status(),
                })
            }]
        }

    # Get SAN before pushing (for cleaner notation)
    san = _board.san(parsed)
    uci = parsed.uci()

    _board.push(parsed)

    turn = "white" if _board.turn == chess.WHITE else "black"

    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "valid": True,
                "san": san,
                "uci": uci,
                "fen": _board.fen(),
                "game_status": _game_status(),
                "turn": turn,
            })
        }]
    }


@tool("get_position", "Get the current board position as FEN.", {})
async def get_position(args: dict[str, Any]) -> dict[str, Any]:
    """Return current board state."""
    turn = "white" if _board.turn == chess.WHITE else "black"
    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "fen": _board.fen(),
                "game_status": _game_status(),
                "turn": turn,
            })
        }]
    }


@tool("get_legal_moves", "Get all legal moves in the current position.", {})
async def get_legal_moves(args: dict[str, Any]) -> dict[str, Any]:
    """List all legal moves."""
    moves = [_board.san(m) for m in _board.legal_moves]
    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "legal_moves": moves,
                "count": len(moves),
            })
        }]
    }


def create_board_mcp_server():
    """Create the chessplaza board MCP server."""
    return create_sdk_mcp_server(
        name="plaza",
        version="1.0.0",
        tools=[new_game, make_move, get_position, get_legal_moves]
    )
