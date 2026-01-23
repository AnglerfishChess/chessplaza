"""LLM evaluation tests for hustler personalities.

These tests use Claude to evaluate that AI-generated responses
stay in character. Skip with: pytest -m 'not llm'
"""

from typing import Callable

import pytest
from claude_agent_sdk import ResultMessage

from pytest_claude_agent_sdk import SpyClaudeSDKClient

from chessplaza.hustler import FAST_EDDIE, VIKTOR, Hustler


# Test cases: (hustler, scenario, judge_question, expected_answer)
PERSONALITY_CASES = [
    # Fast Eddie - NYC street hustler style
    (
        FAST_EDDIE,
        "Greet a new opponent who just sat down.",
        "Does this sound like a cocky NYC street chess hustler with slang and short punchy sentences?",
        "YES",
    ),
    (
        FAST_EDDIE,
        "React to opponent playing a weak opening move (1.f3).",
        "Does this sound like a trash-talking street hustler mocking a bad move?",
        "YES",
    ),
    # Viktor - dignified old Russian
    (
        VIKTOR,
        "Answer the question: 'Were you ever a professional chess player?'",
        "Does this sound like a dignified old Russian deflecting questions about his past?",
        "YES",
    ),
    (
        VIKTOR,
        "Comment on the beauty of a well-played endgame.",
        "Does this sound philosophical and melancholic, like an old chess master reminiscing?",
        "YES",
    ),
]


@pytest.mark.llm
class TestHustlerPersonalities:
    """Test that hustler prompts produce appropriate personality responses."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("hustler,scenario,judge_q,expected", PERSONALITY_CASES)
    async def test_hustler_in_character(
        self,
        hustler: Hustler,
        scenario: str,
        judge_q: str,
        expected: str,
        claude_client: SpyClaudeSDKClient,
        claude_judge_client: Callable,
    ) -> None:
        """Hustler response should match their personality."""
        # Generate response in character
        prompt = f"{hustler.prompt}\n\n{scenario}"

        response_text = ""
        async for msg in claude_client.query(prompt):
            if isinstance(msg, ResultMessage) and msg.result:
                response_text = msg.result

        claude_client.assert_called_once()
        assert len(response_text) > 0

        # Judge evaluates the response
        judge_prompt = f"""Evaluate this response:
"{response_text}"

{judge_q}
Answer only YES or NO."""

        judge_result = ""
        async for msg in claude_judge_client(prompt=judge_prompt):
            if isinstance(msg, ResultMessage) and msg.result:
                judge_result = msg.result

        assert expected in judge_result.upper()

    @pytest.mark.asyncio
    async def test_personalities_are_distinct(
        self,
        claude_client: SpyClaudeSDKClient,
        claude_judge_client: Callable,
    ) -> None:
        """Different hustlers should have noticeably different styles."""
        # Get greeting from Fast Eddie
        eddie_response = ""
        async for msg in claude_client.query(f"{FAST_EDDIE.prompt}\n\nGreet a new opponent briefly."):
            if isinstance(msg, ResultMessage) and msg.result:
                eddie_response = msg.result

        claude_client.reset_calls()

        # Get greeting from Viktor
        viktor_response = ""
        async for msg in claude_client.query(f"{VIKTOR.prompt}\n\nGreet a new opponent briefly."):
            if isinstance(msg, ResultMessage) and msg.result:
                viktor_response = msg.result

        # Judge determines if responses are stylistically distinct
        judge_prompt = f"""Two chess players greet an opponent:

A: "{eddie_response}"
B: "{viktor_response}"

Are these noticeably different in style and personality?
Answer only YES or NO."""

        judge_result = ""
        async for msg in claude_judge_client(prompt=judge_prompt):
            if isinstance(msg, ResultMessage) and msg.result:
                judge_result = msg.result

        assert "YES" in judge_result.upper()
