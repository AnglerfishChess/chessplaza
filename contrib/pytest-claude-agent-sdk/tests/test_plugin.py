"""Tests for pytest-claude-agent-sdk plugin."""

from typing import Callable

import pytest
from claude_agent_sdk import ResultMessage

from pytest_claude_agent_sdk import SpyClaudeSDKClient


class TestFixtureTypes:
    """Test that fixtures provide correct types (no LLM calls)."""

    def test_claude_query_is_callable(self, claude_query: Callable) -> None:
        assert callable(claude_query)

    def test_claude_client_is_spy(self, claude_client: SpyClaudeSDKClient) -> None:
        assert isinstance(claude_client, SpyClaudeSDKClient)

    def test_claude_judge_client_is_callable(self, claude_judge_client: Callable) -> None:
        assert callable(claude_judge_client)

    def test_client_and_judge_are_different_fixtures(
        self,
        claude_client: SpyClaudeSDKClient,
        claude_judge_client: Callable,
    ) -> None:
        # They're different types - client is a spy, judge is a function
        assert isinstance(claude_client, SpyClaudeSDKClient)
        assert callable(claude_judge_client)
        assert not isinstance(claude_judge_client, SpyClaudeSDKClient)


class TestSpyFunctionality:
    """Test spy functionality without making LLM calls."""

    def test_spy_starts_with_no_calls(
        self, claude_client: SpyClaudeSDKClient
    ) -> None:
        assert claude_client.call_count == 0
        assert claude_client.calls == []
        assert claude_client.last_call is None

    def test_assert_not_called_passes_when_no_calls(
        self, claude_client: SpyClaudeSDKClient
    ) -> None:
        claude_client.assert_not_called()

    def test_assert_called_fails_when_no_calls(
        self, claude_client: SpyClaudeSDKClient
    ) -> None:
        with pytest.raises(AssertionError, match="Expected at least one call"):
            claude_client.assert_called()

    def test_assert_called_once_fails_when_no_calls(
        self, claude_client: SpyClaudeSDKClient
    ) -> None:
        with pytest.raises(AssertionError, match="Expected exactly one call"):
            claude_client.assert_called_once()

    def test_reset_calls(self, claude_client: SpyClaudeSDKClient) -> None:
        # Manually add a fake call record for testing
        from pytest_claude_agent_sdk import CallRecord
        claude_client.calls.append(CallRecord(prompt="test"))
        assert claude_client.call_count == 1

        claude_client.reset_calls()
        assert claude_client.call_count == 0


class TestMarkers:
    """Test that markers work correctly."""

    @pytest.mark.llm
    def test_llm_marker_exists(self) -> None:
        """This test is marked with @pytest.mark.llm."""
        pass


@pytest.mark.llm
class TestLLMCalls:
    """Tests that actually call the LLM. Skip with: pytest -m 'not llm'"""

    @pytest.mark.asyncio
    async def test_claude_query_works(self, claude_query: Callable) -> None:
        async for msg in claude_query(prompt="Reply with exactly one word: HELLO"):
            if isinstance(msg, ResultMessage):
                assert msg.result is not None
                assert "HELLO" in msg.result.upper()

    @pytest.mark.asyncio
    async def test_claude_client_records_calls(
        self, claude_client: SpyClaudeSDKClient
    ) -> None:
        # Make a query
        async for msg in claude_client.query("Reply with exactly one word: WORLD"):
            if isinstance(msg, ResultMessage):
                assert msg.result is not None
                assert "WORLD" in msg.result.upper()

        # Verify spy recorded it
        claude_client.assert_called_once()
        assert claude_client.call_count == 1
        assert "WORLD" in claude_client.calls[0].prompt
        assert claude_client.last_call is not None
        assert claude_client.last_call.response is not None

    @pytest.mark.asyncio
    async def test_spy_assertion_helpers(
        self, claude_client: SpyClaudeSDKClient
    ) -> None:
        # Make a query
        async for _ in claude_client.query("What is the meaning of life?"):
            pass

        # Test assertion helpers
        claude_client.assert_called()
        claude_client.assert_called_once()
        claude_client.assert_call_count(1)
        claude_client.assert_any_call_contains("meaning")
        claude_client.assert_last_call_contains("life")

    @pytest.mark.asyncio
    async def test_claude_judge_client_works(
        self, claude_judge_client: Callable
    ) -> None:
        async for msg in claude_judge_client(prompt="Is 2+2=4? Answer YES or NO only."):
            if isinstance(msg, ResultMessage):
                assert msg.result is not None
                assert "YES" in msg.result.upper()
