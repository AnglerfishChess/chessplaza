"""pytest-claude-agent-sdk: Pytest plugin for testing with Claude Agent SDK."""

from pytest_claude_agent_sdk.spy import CallRecord, SpyClaudeSDKClient

__version__ = "0.1.0"

__all__ = [
    "CallRecord",
    "SpyClaudeSDKClient",
    "__version__",
]
