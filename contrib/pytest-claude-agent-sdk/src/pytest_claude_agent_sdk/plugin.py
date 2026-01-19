"""pytest-claude-agent-sdk: Pytest plugin entry point."""

import pytest

# Import fixtures so they're registered with pytest
from pytest_claude_agent_sdk.fixtures import (  # noqa: F401
    claude_client,
    claude_judge_client,
    claude_query,
)

# Re-export types for user convenience
from pytest_claude_agent_sdk.spy import CallRecord, SpyClaudeSDKClient  # noqa: F401

__all__ = [
    # Fixtures
    "claude_client",
    "claude_judge_client",
    "claude_query",
    # Types
    "CallRecord",
    "SpyClaudeSDKClient",
]


def pytest_configure(config: pytest.Config) -> None:
    """Register the 'llm' marker."""
    config.addinivalue_line(
        "markers",
        "llm: mark test as requiring LLM calls (may be slow/costly)",
    )
