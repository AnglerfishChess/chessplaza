"""Unit tests for chessplaza.hustler."""

import pytest

from chessplaza.hustler import _elo_to_skill_level


class TestEloToSkillLevel:
    """Tests for _elo_to_skill_level conversion."""

    @pytest.mark.parametrize(
        "elo,expected_skill",
        [
            (1000, 0),  # Minimum ELO -> skill 0
            (1090, 1),  # Just above threshold
            (1500, 5),  # Mid-range
            (2000, 11),  # Strong club player
            (2800, 20),  # Super GM -> max skill
        ],
    )
    def test_elo_conversion(self, elo: int, expected_skill: int):
        """Should convert ELO to skill level correctly."""
        assert _elo_to_skill_level(elo) == expected_skill

    def test_clamps_to_minimum(self):
        """Should clamp to 0 for very low ELO."""
        assert _elo_to_skill_level(500) == 0
        assert _elo_to_skill_level(0) == 0

    def test_clamps_to_maximum(self):
        """Should clamp to 20 for very high ELO."""
        assert _elo_to_skill_level(3000) == 20
        assert _elo_to_skill_level(5000) == 20
