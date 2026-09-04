"""Unit tests for chessplaza.board."""

import json
from collections.abc import Iterator
from typing import Any

import pytest

from chessplaza import board

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# Both rooks and both kings home, nothing in between: every castling is legal here.
CASTLING_FEN = "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"

# White Kg5, Qf7 against a lone Kh8. Kg6 takes g7, g8 and h7 without checking h8.
STALEMATE_IN_ONE_FEN = "7k/5Q2/8/6K1/8/8/8/8 w - - 0 1"

# 1.Nf3 Nf6 2.Ng1 Ng8 3.Nf3 Nf6 4.Ng1 Ng8: the start position stands for the third time.
REPETITION_LINE = ["Nf3", "Nf6", "Ng1", "Ng8", "Nf3", "Nf6", "Ng1", "Ng8"]

FOOLS_MATE = ["f3", "e5", "g4", "Qh4"]


@pytest.fixture(autouse=True)
def _fresh_board() -> Iterator[None]:
    """Give every test the starting position, and leave it that way."""
    board._game = board._new_game()
    yield
    board._game = board._new_game()


def _set_position(fen: str) -> None:
    """Put the module's game at `fen`."""
    board._game = board._new_game(fen)


async def _call(tool: Any, **args: Any) -> dict[str, Any]:
    """Invoke an MCP tool handler and read its JSON payload back."""
    result = await tool.handler(args)
    return json.loads(result["content"][0]["text"])


async def _play(*moves: str) -> dict[str, Any]:
    """Play a line, returning the answer to the last move."""
    answer: dict[str, Any] = {}
    for move in moves:
        answer = await _call(board.make_move, move=move)
        assert answer["valid"], answer
    return answer


class TestNewGame:
    """A new game starts from the initial position."""

    @pytest.mark.asyncio
    async def test_resets_to_start(self) -> None:
        await _play("e4")
        assert await _call(board.new_game) == {
            "fen": START_FEN,
            "game_status": "ongoing",
            "turn": "white",
            "opening": None,
        }


class TestMakeMove:
    """Moves arrive in either notation and come back in both."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("move", "san", "uci", "fen", "opening"),
        [
            (
                "e4",
                "e4",
                "e2e4",
                "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
                "King's Pawn Game",
            ),
            (
                "e2e4",
                "e4",
                "e2e4",
                "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
                "King's Pawn Game",
            ),
            (
                "Nf3",
                "Nf3",
                "g1f3",
                "rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 1 1",
                "Zukertort Opening",
            ),
            (
                "g1f3",
                "Nf3",
                "g1f3",
                "rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 1 1",
                "Zukertort Opening",
            ),
        ],
    )
    async def test_san_and_uci_accepted(self, move: str, san: str, uci: str, fen: str, opening: str) -> None:
        assert await _call(board.make_move, move=move) == {
            "valid": True,
            "san": san,
            "uci": uci,
            "fen": fen,
            "game_status": "ongoing",
            "turn": "black",
            "opening": opening,
        }

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "move",
        [
            "e5",  # well-formed SAN, but Black's pawn is not White's to move
            "e2e5",  # a pawn does not reach e5 in one move from e2
            "Ke2",  # the king's own pawn stands there
            "zzz",  # not notation at all
            "",  # nothing at all
        ],
    )
    async def test_rejects_move(self, move: str) -> None:
        answer = await _call(board.make_move, move=move)
        assert answer["valid"] is False
        assert move in answer["error"]
        assert answer["fen"] == START_FEN
        assert answer["game_status"] == "ongoing"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("move", "san", "uci"),
        [
            ("O-O", "O-O", "e1g1"),
            ("O-O-O", "O-O-O", "e1c1"),
            ("e1g1", "O-O", "e1g1"),
        ],
    )
    async def test_castling(self, move: str, san: str, uci: str) -> None:
        _set_position(CASTLING_FEN)
        answer = await _call(board.make_move, move=move)
        assert (answer["san"], answer["uci"]) == (san, uci)


class TestGameStatus:
    """Terminal positions are named, claimable draws included."""

    @pytest.mark.asyncio
    async def test_checkmate(self) -> None:
        answer = await _play(*FOOLS_MATE)
        assert answer["san"] == "Qh4#"
        assert answer["game_status"] == "checkmate"

    @pytest.mark.asyncio
    async def test_stalemate(self) -> None:
        _set_position(STALEMATE_IN_ONE_FEN)
        assert (await _play("Kg6"))["game_status"] == "stalemate"

    @pytest.mark.asyncio
    async def test_threefold_repetition_is_a_draw(self) -> None:
        answers = [await _call(board.make_move, move=move) for move in REPETITION_LINE]
        assert [a["game_status"] for a in answers[:-1]] == ["ongoing"] * (len(REPETITION_LINE) - 1)
        assert answers[-1]["game_status"] == "draw"

    @pytest.mark.asyncio
    async def test_insufficient_material_is_a_draw(self) -> None:
        _set_position("8/8/8/4k3/8/8/4K3/8 w - - 0 1")
        assert (await _call(board.get_position))["game_status"] == "draw"


class TestGetPosition:
    """The position tool reports what the last move left behind."""

    @pytest.mark.asyncio
    async def test_reports_current_state(self) -> None:
        await _play("e4", "e5")
        assert await _call(board.get_position) == {
            "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
            "game_status": "ongoing",
            "turn": "white",
            "opening": "King's Pawn Game",
        }


class TestGetLegalMoves:
    """Legal moves come back in SAN."""

    @pytest.mark.asyncio
    async def test_twenty_at_the_start(self) -> None:
        answer = await _call(board.get_legal_moves)
        assert answer["count"] == 20
        assert len(answer["legal_moves"]) == 20
        assert {"e4", "e3", "Nf3", "Nh3"} <= set(answer["legal_moves"])

    @pytest.mark.asyncio
    async def test_none_after_checkmate(self) -> None:
        await _play(*FOOLS_MATE)
        assert await _call(board.get_legal_moves) == {"legal_moves": [], "count": 0}
