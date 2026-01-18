"""Unit tests for chessplaza.__main__."""

from datetime import datetime

import pytest

from chessplaza.__main__ import _get_park_time


class TestGetParkTime:
    """Tests for _get_park_time function."""

    @pytest.mark.parametrize(
        "hour,expected_time_of_day",
        [
            # Night hours clamped to late evening
            (0, "late evening"),
            (3, "late evening"),
            (5, "late evening"),
            (22, "late evening"),
            (23, "late evening"),
            # Normal day hours
            (6, "early morning"),
            (8, "early morning"),
            (9, "morning"),
            (11, "morning"),
            (12, "midday"),
            (13, "midday"),
            (14, "afternoon"),
            (16, "afternoon"),
            (17, "evening"),
            (19, "evening"),
            (20, "late evening"),
            (21, "late evening"),
        ],
    )
    def test_time_of_day_by_hour(self, hour: int, expected_time_of_day: str):
        """Should return correct time_of_day based on hour."""
        test_datetime = datetime(2025, 1, 15, hour, 30, 0)
        result = _get_park_time(now=test_datetime)
        assert result["time_of_day"] == expected_time_of_day

    def test_returns_date_and_day_of_week(self):
        """Should include formatted date and day of week."""
        test_datetime = datetime(2025, 1, 15, 14, 0, 0)  # Wednesday
        result = _get_park_time(now=test_datetime)
        assert result["date"] == "January 15"
        assert result["day_of_week"] == "Wednesday"

    def test_defaults_to_now_when_no_argument(self):
        """Should use current time when now is not provided."""
        result = _get_park_time()
        assert "time_of_day" in result
        assert "date" in result
        assert "day_of_week" in result
