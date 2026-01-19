# pytest-claude-agent-sdk

Pytest plugin for working with [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python).

Three complementary use cases:

1. **Test apps that use Claude Agent SDK** - your app uses Claude internally, and you need to test it
2. **Test apps using Claude Agent SDK** - use Claude as a smart test oracle (LLM-as-judge)
3. **Both at once** - test your Claude-powered app with Claude-powered assertions

Uses Claude Code authentication automatically - no API key management needed.

## Installation

```bash
pip install pytest-claude-agent-sdk
```

## Fixtures

| Fixture | Type | Purpose |
|---------|------|---------|
| `claude_query` | `QueryFunc` | Substitute for `query()` - stateless |
| `claude_client` | `SpyClaudeSDKClient` | Client-like interface for app under test (with spy) |
| `claude_judge_client` | `QueryFunc` | Separate query function for evaluation |

`QueryFunc = Callable[..., AsyncIterator[Message]]` - matches `claude_agent_sdk.query()` signature.

## SpyClaudeSDKClient

The `claude_client` fixture provides a `SpyClaudeSDKClient` - wraps `query()` with call recording:

```python
import pytest
from pytest_claude_agent_sdk import SpyClaudeSDKClient


@pytest.mark.llm
@pytest.mark.asyncio
async def test_my_app(claude_client: SpyClaudeSDKClient) -> None:
    # Use it like query() - real LLM calls happen
    async for msg in claude_client.query("Hello"):
        pass

    # Inspect what happened
    assert claude_client.call_count == 1
    assert "Hello" in claude_client.calls[0].prompt
    assert claude_client.last_call.response is not None

    # Use assertion helpers
    claude_client.assert_called_once()
    claude_client.assert_any_call_contains("Hello")
```

### Spy Attributes

- `calls: list[CallRecord]` - All calls made
- `call_count: int` - Number of calls
- `last_call: CallRecord | None` - Most recent call

### Spy Assertion Helpers

- `assert_called()` - At least one call was made
- `assert_not_called()` - No calls were made
- `assert_called_once()` - Exactly one call was made
- `assert_call_count(n)` - Exactly n calls were made
- `assert_any_call_contains(substring)` - Some call's prompt contains substring
- `assert_last_call_contains(substring)` - Last call's prompt contains substring
- `reset_calls()` - Clear call history

## Examples

### 1. Testing an app that uses Claude

Your app has a function that accepts something with a `query()` method. Test it with the spy client:

**your_app/greeter.py**
```python
from typing import Protocol, AsyncIterator

from claude_agent_sdk import Message, ResultMessage


class QueryClient(Protocol):
    """Protocol for anything with a query() method."""
    def query(self, prompt: str) -> AsyncIterator[Message]: ...


async def generate_greeting(client: QueryClient, name: str) -> str:
    async for msg in client.query(f"Generate a short greeting for {name}"):
        if isinstance(msg, ResultMessage):
            return msg.result or ""
    return ""
```

**tests/test_greeter.py**
```python
import pytest
from pytest_claude_agent_sdk import SpyClaudeSDKClient

from your_app.greeter import generate_greeting


@pytest.mark.llm
@pytest.mark.asyncio
async def test_greeting(claude_client: SpyClaudeSDKClient) -> None:
    greeting: str = await generate_greeting(claude_client, "Alice")

    # Verify the output
    assert len(greeting) > 0
    assert "alice" in greeting.lower()

    # Verify the call was made correctly
    claude_client.assert_called_once()
    claude_client.assert_last_call_contains("Alice")
```

### 2. Testing any app using Claude as judge

Your app doesn't use Claude, but you want Claude to evaluate outputs:

**your_app/email.py**
```python
def format_email(subject: str, body: str) -> str:
    return f"Subject: {subject}\n\n{body}\n\nBest regards"
```

**tests/test_email.py**
```python
from typing import Callable

import pytest
from claude_agent_sdk import ResultMessage

from your_app.email import format_email


@pytest.mark.llm
@pytest.mark.asyncio
async def test_email_is_professional(claude_judge_client: Callable) -> None:
    email: str = format_email("Meeting", "Let's meet tomorrow at 3pm.")

    async for msg in claude_judge_client(
        prompt=f"Is this email professional? Answer only YES or NO.\n\n{email}"
    ):
        if isinstance(msg, ResultMessage):
            assert msg.result is not None
            assert "YES" in msg.result.upper()
```

### 3. Both: Test Claude app with Claude judge

Your app uses Claude, and you evaluate it with Claude (separate fixture):

**chess_hustler/trash_talk.py**
```python
from typing import Protocol, AsyncIterator

from claude_agent_sdk import Message, ResultMessage


class QueryClient(Protocol):
    """Protocol for anything with a query() method."""
    def query(self, prompt: str) -> AsyncIterator[Message]: ...


async def trash_talk(client: QueryClient, move: str) -> str:
    async for msg in client.query(
        f"You're a NYC chess hustler. React to opponent's move: {move}"
    ):
        if isinstance(msg, ResultMessage):
            return msg.result or ""
    return ""
```

**tests/test_trash_talk.py**
```python
from typing import Callable

import pytest
from claude_agent_sdk import ResultMessage

from pytest_claude_agent_sdk import SpyClaudeSDKClient

from chess_hustler.trash_talk import trash_talk


@pytest.mark.llm
@pytest.mark.asyncio
async def test_trash_talk_is_in_character(
    claude_client: SpyClaudeSDKClient,
    claude_judge_client: Callable,
) -> None:
    # Generate with app client (spy)
    response: str = await trash_talk(claude_client, "e4")

    # Verify the call was made
    claude_client.assert_called_once()
    claude_client.assert_any_call_contains("e4")

    # Evaluate with judge (separate fixture, not spied)
    async for msg in claude_judge_client(
        prompt=f"Does this sound like a sarcastic NYC chess hustler? YES or NO.\n\n{response}"
    ):
        if isinstance(msg, ResultMessage):
            assert msg.result is not None
            assert "YES" in msg.result.upper()
```

## Markers

```python
@pytest.mark.llm  # Mark tests that call LLM
```

```bash
pytest -m llm        # Run only LLM tests
pytest -m "not llm"  # Skip LLM tests (fast CI)
```

## License

MIT
