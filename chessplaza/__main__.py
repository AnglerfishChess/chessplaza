"""
Entry point for chessplaza.

Supports running via:
  - uvx chessplaza (after PyPI publish)
  - uv run chessplaza (local development)
  - python -m chessplaza
"""

import asyncio
import json
import random

import click

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, TextBlock

from chessplaza import __version__
from chessplaza.hustler import (
    HUSTLERS,
    Hustler,
    get_hustler_prompt,
    get_park_prompt,
)

# Track if we've shown the interaction hint
_hint_shown: bool = False

# Voice module is optional - imported lazily only when --voice is used
# because edge-tts and miniaudio may not be installed


@click.command()
@click.version_option(version=__version__, prog_name="chessplaza")
@click.option("--language", "-l", default="English", help="Language for the experience (e.g., Russian, Spanish, Chinese)")
@click.option("--voice", "-v", is_flag=True, help="Enable text-to-speech (requires voice extras)")
def main(language: str, voice: bool):
    """Welcome to Chess Plaza - play against AI chess hustlers with personality."""
    # Voice check - lazy import because it's optional
    if voice:
        try:
            from chessplaza.voice import is_voice_available
            if not is_voice_available():
                click.echo("Voice support not available. Install with: uv pip install -e '.[voice]'", err=True)
                return
        except ImportError:
            click.echo("Voice support not available. Install with: uv pip install -e '.[voice]'", err=True)
            return

    asyncio.run(_play_loop(language, voice))


async def _play_loop(language: str, voice_enabled: bool):
    """Main game loop."""
    click.echo()
    click.secho("=== Welcome to Chess Plaza ===", fg="cyan", bold=True)
    click.echo()

    while True:
        # Park phase - select a hustler
        hustler = await _park_phase(language, voice_enabled)
        if hustler is None:
            # User wants to leave the park
            click.secho("\nYou leave the park. The sounds of chess fade behind you...", dim=True)
            break

        # Dialog phase with selected hustler
        leave_park = await _dialog_phase(hustler, language, voice_enabled)
        if leave_park:
            click.secho("\nYou leave the park. The sounds of chess fade behind you...", dim=True)
            break
        # Otherwise, back to park to select another hustler


async def _park_phase(language: str, voice_enabled: bool) -> Hustler | None:
    """Park scene - describe the park and let user select a hustler.

    Returns the selected Hustler, or None if user wants to leave the park.
    """
    options = ClaudeAgentOptions(
        system_prompt=get_park_prompt(language),
        max_turns=1,
        allowed_tools=[],
    )

    global _hint_shown

    # Initial park description
    async with ClaudeSDKClient(options=options) as client:
        await client.query("I just entered the park. Describe what I see.")

        response = await _get_response(client)
        await _display_response(response, voice_enabled, None)

        # Show hint only once per session
        if not _hint_shown:
            random_hustler = random.choice(list(HUSTLERS.values()))
            click.echo()
            click.secho(f"(Just say what you want to do, e.g., \"I'll go talk to {random_hustler.name}\")", dim=True)
            _hint_shown = True

        # Selection loop
        while True:
            user_input = click.prompt("\nYou", prompt_suffix="> ")

            if _is_leaving_park(user_input):
                return None

            await client.query(user_input)
            response = await _get_response(client)
            await _display_response(response, voice_enabled, None)

            # Check if we're approaching someone
            next_action = response.get("next_action", "select_hustler")
            if next_action.startswith("approach_"):
                hustler_id = next_action.replace("approach_", "")
                if hustler_id in HUSTLERS:
                    return HUSTLERS[hustler_id]


async def _dialog_phase(hustler: Hustler, language: str, voice_enabled: bool) -> bool:
    """Dialog loop with a specific hustler.

    Returns True if user wants to leave the park entirely, False to go back to park.
    """
    click.echo()
    click.secho(f"--- Talking to {hustler.name} ---", fg="yellow", bold=True)
    click.echo()

    options = ClaudeAgentOptions(
        system_prompt=get_hustler_prompt(hustler, language),
        max_turns=1,
        allowed_tools=[],
    )

    async with ClaudeSDKClient(options=options) as client:
        # Initial greeting from the hustler
        await client.query("Someone just sat down at your table. Greet them.")

        response = await _get_response(client)
        await _display_response(response, voice_enabled, hustler)

        # Dialog loop
        while True:
            user_input = click.prompt("\nYou", prompt_suffix="> ")
            await client.query(user_input)

            response = await _get_response(client)
            await _display_response(response, voice_enabled, hustler)

            intent = response.get("player_intent", "continue")

            if intent == "leaving_park":
                # Hustler detected user wants to leave park - confirm
                user_confirm = click.prompt("\nYou", prompt_suffix="> ")
                await client.query(user_confirm)
                response = await _get_response(client)
                await _display_response(response, voice_enabled, hustler)

                new_intent = response.get("player_intent", "continue")
                if new_intent == "leaving_park":
                    return True  # Leave park
                elif new_intent == "leaving_opponent":
                    return False  # Back to park
                # else: stay with this hustler

            elif intent == "leaving_opponent":
                # Hustler detected user wants to leave this table - confirm
                user_confirm = click.prompt("\nYou", prompt_suffix="> ")
                await client.query(user_confirm)
                response = await _get_response(client)
                await _display_response(response, voice_enabled, hustler)

                new_intent = response.get("player_intent", "continue")
                if new_intent in ("leaving_opponent", "leaving_park"):
                    if new_intent == "leaving_park":
                        return True
                    return False  # Back to park
                # else: stay with this hustler


async def _get_response(client: ClaudeSDKClient) -> dict:
    """Get response from client and parse JSON."""
    full_text = ""

    async for msg in client.receive_response():
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    full_text += block.text

    # Try to parse as JSON
    try:
        # Clean up potential markdown code blocks
        text = full_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        return json.loads(text.strip())
    except json.JSONDecodeError:
        # Fallback: treat as plain spoken text
        return {
            "narrative": "",
            "spoken_display": full_text,
            "spoken_tts": full_text,
            "player_intent": "continue",
        }


async def _display_response(response: dict, voice_enabled: bool, hustler: Hustler | None):
    """Display the structured response and optionally speak it."""
    narrative = response.get("narrative", "")
    spoken_display = response.get("spoken_display", "")
    spoken_tts = response.get("spoken_tts", "")
    speaker_id = response.get("speaker", "")

    # Determine who is speaking (for voice and display)
    speaker = hustler
    if not speaker and speaker_id and speaker_id in HUSTLERS:
        speaker = HUSTLERS[speaker_id]

    # Print narrative in dim/italic
    if narrative:
        click.secho(narrative, dim=True, italic=True)

    # Print spoken words
    if spoken_display:
        if speaker:
            click.secho(f"{speaker.name}: ", fg="green", bold=True, nl=False)
        click.echo(spoken_display)

    # Speak if voice enabled and a hustler is speaking (not narrator)
    if voice_enabled and spoken_tts and speaker:
        from chessplaza.voice import speak
        await speak(spoken_tts, speaker.voice)


def _is_leaving_park(text: str) -> bool:
    """Quick check if user wants to leave the park from the park selection phase."""
    text_lower = text.lower()
    leave_phrases = ["leave", "exit", "quit", "go home", "goodbye", "bye", "i'm out", "gotta go"]
    return any(phrase in text_lower for phrase in leave_phrases)


if __name__ == "__main__":
    main()