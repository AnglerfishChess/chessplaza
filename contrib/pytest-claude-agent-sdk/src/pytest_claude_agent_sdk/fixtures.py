"""Pytest fixtures for Claude Agent SDK."""

from typing import AsyncIterator, Callable

import pytest
from claude_agent_sdk import Message, ResultMessage, query as sdk_query

from pytest_claude_agent_sdk.spy import SpyClaudeSDKClient


# Type alias for the query function
# The actual signature is: query(*, prompt: str, options: ClaudeAgentOptions | None, ...) -> AsyncIterator[Message]
# Since Python's Callable can't express keyword-only args, we use ... for arguments
QueryFunc = Callable[..., AsyncIterator[Message]]


@pytest.fixture
def claude_query() -> QueryFunc:
    """Substitute for `claude_agent_sdk.query()`.

    Stateless async function for simple queries. Can be used for any purpose:
    app logic, judging, test data generation, etc.

    Note: This is an async generator. Use with pytest-asyncio:

        @pytest.mark.asyncio
        async def test_simple(claude_query):
            async for msg in claude_query(prompt="What is 2 + 2?"):
                if isinstance(msg, ResultMessage):
                    assert "4" in msg.result
    """
    return sdk_query


@pytest.fixture
def claude_client() -> SpyClaudeSDKClient:
    """SpyClaudeSDKClient instance for app under test.

    Provides a client-like interface wrapping claude_agent_sdk.query().
    All calls go through to the LLM, but are also recorded for inspection.

    No connect/disconnect needed - each query() call handles its own connection.

    Attributes:
        calls: List of CallRecord objects for all queries made.
        call_count: Number of queries made.
        last_call: Most recent CallRecord.

    Assertion helpers:
        assert_called(), assert_not_called(), assert_called_once(),
        assert_call_count(n), assert_any_call_contains(substring),
        assert_last_call_contains(substring), reset_calls()

    Example:
        @pytest.mark.asyncio
        async def test_my_function(claude_client: SpyClaudeSDKClient):
            await my_function(claude_client)

            assert claude_client.call_count == 1
            assert "hello" in claude_client.calls[0].prompt
            claude_client.assert_called_once()
    """
    return SpyClaudeSDKClient()


@pytest.fixture
def claude_judge_client() -> QueryFunc:
    """Separate query function for LLM-as-judge evaluations.

    Use this to evaluate outputs from your app. Kept as a separate fixture
    for clear separation of concerns:
    - Clear distinction between "app under test" and "test oracle"
    - Could be configured differently in the future (different model, etc.)

    Note: This is the raw query function, not a spy. We don't need to
    inspect judge calls - they're part of the test infrastructure.

    Example:
        @pytest.mark.asyncio
        async def test_quality(claude_client, claude_judge_client):
            output = await my_app(claude_client, input)
            async for msg in claude_judge_client(prompt=f"Is this good? {output}"):
                if isinstance(msg, ResultMessage):
                    assert "YES" in msg.result.upper()
    """
    return sdk_query
