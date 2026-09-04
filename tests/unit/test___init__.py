"""Unit tests for the chessplaza package metadata."""

from importlib.metadata import version

import chessplaza


def test_version_matches_distribution() -> None:
    """`__version__` and the version the distribution declares are one number."""
    assert chessplaza.__version__ == version("chessplaza")
