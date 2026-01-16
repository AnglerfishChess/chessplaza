"""
Entry point for chessplaza.

Supports running via:
  - uvx chessplaza (after PyPI publish)
  - uv run chessplaza (local development)
  - python -m chessplaza
"""

import asyncio
from datetime import datetime
import json
import random

import click

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, TextBlock

from chessplaza import __version__
from chessplaza.board import create_board_mcp_server
from chessplaza.hustler import (
    HUSTLERS,
    Hustler,
    get_unified_game_prompt,
)

# Track if we've shown the interaction hint
_hint_shown: bool = False


def _get_park_time() -> dict[str, str]:
    """Get current date/time info for park atmosphere.

    Night hours (22:00-06:00) are treated as late evening.
    """
    now = datetime.now()

    # Clamp night to late evening
    hour = now.hour
    if hour >= 22 or hour < 6:
        time_of_day = "late evening"
    elif hour < 9:
        time_of_day = "early morning"
    elif hour < 12:
        time_of_day = "morning"
    elif hour < 14:
        time_of_day = "midday"
    elif hour < 17:
        time_of_day = "afternoon"
    elif hour < 20:
        time_of_day = "evening"
    else:
        time_of_day = "late evening"

    return {
        "date": now.strftime("%B %d"),  # e.g., "January 15"
        "day_of_week": now.strftime("%A"),  # e.g., "Tuesday"
        "time_of_day": time_of_day,
    }

# Voice module is optional - imported lazily only when --voice is used
# because edge-tts and miniaudio may not be installed


@click.command()
@click.version_option(version=__version__, prog_name="chessplaza")
@click.argument("engine", type=click.Path(exists=True))
@click.option("--language", "-l", default="English", help="Language for the experience (e.g., Russian, Spanish, Chinese)")
@click.option("--voice", "-v", is_flag=True, help="Enable text-to-speech (requires voice extras)")
@click.option("--use-github-deps", is_flag=True, help="Use bleeding-edge GitHub versions of dependencies instead of PyPI")
@click.option("--prototype", is_flag=True, help="Run the chat game UI prototype instead of the main game")
@click.option("--gui", is_flag=True, help="Use PySide6 GUI (only with --prototype)")
def main(engine: str, language: str, voice: bool, use_github_deps: bool, prototype: bool, gui: bool):
    """Welcome to Chess Plaza - play against AI chess hustlers with personality.

    ENGINE is the path to a UCI-compatible chess engine (e.g., /usr/local/bin/stockfish).
    """
    # Prototype mode - run the UI prototype instead of the main game
    if prototype:
        from chessplaza.prototype import run_prototype
        run_prototype(gui=gui)
        return

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

    asyncio.run(_play_loop(engine, language, voice, use_github_deps))


# GitHub URLs for latest development versions of dependencies
_GITHUB_DEPS = {
    "chess-uci-mcp": "git+https://github.com/AnglerfishChess/chess-uci-mcp",
}


async def _play_loop(engine_path: str, language: str, voice_enabled: bool, use_github_deps: bool = False):
    """Main game loop."""
    click.echo()
    click.secho("=== Welcome to Chess Plaza ===", fg="cyan", bold=True)
    click.echo()

    leave_park_text = "You leave the park. The sounds of chess fade behind you..."

    # Configure chess engine MCP server
    if use_github_deps:
        mcp_args = ["--from", _GITHUB_DEPS["chess-uci-mcp"], "chess-uci-mcp", engine_path]
    else:
        mcp_args = ["chess-uci-mcp", engine_path]

    mcp_servers = {
        # External: chess engine via chess-uci-mcp
        "chess": {
            "type": "stdio",
            "command": "uvx",
            "args": mcp_args,
        },
        # Internal: board state via python-chess
        "plaza": create_board_mcp_server(),
    }

    allowed_tools = [
        # chess-uci-mcp tools (engine)
        "mcp__chess__analyze",
        "mcp__chess__get_best_move",
        "mcp__chess__set_position",
        "mcp__chess__engine_info",
        "mcp__chess__get_engine_options",
        "mcp__chess__set_engine_options",
        # plaza tools (board state)
        "mcp__plaza__new_game",
        "mcp__plaza__make_move",
        "mcp__plaza__get_position",
        "mcp__plaza__get_legal_moves",
    ]

    # Single client for the entire session - maintains conversation history
    park_time = _get_park_time()
    options = ClaudeAgentOptions(
        system_prompt=get_unified_game_prompt(language, park_time),
        mcp_servers=mcp_servers,
        allowed_tools=allowed_tools,
        max_turns=10,  # More turns needed for tool use
        max_thinking_tokens=32768,  # Allow extended thinking for chess reasoning
    )

    async with ClaudeSDKClient(options=options) as client:
        while True:
            # Park phase - select a hustler
            hustler = await _park_phase(client, voice_enabled)
            if hustler is None:
                # User wants to leave the park
                click.secho(f"\n{leave_park_text}", dim=True)
                break

            # Dialog phase with selected hustler
            leave_park = await _dialog_phase(client, hustler, voice_enabled)
            if leave_park:
                click.secho(f"\n{leave_park_text}", dim=True)
                break
            # Otherwise, back to park to select another hustler


async def _park_phase(client: ClaudeSDKClient, voice_enabled: bool) -> Hustler | None:
    """Park scene - describe the park and let user select a hustler.

    Returns the selected Hustler, or None if user wants to leave the park.
    """
    global _hint_shown

    # Initial park description
    await client.query("[NARRATOR] I just entered the park. Describe what I see.")

    response = await _get_response(client)
    await _display_response(response, voice_enabled, None)

    # Show hint only once per session
    if not _hint_shown:
        random_hustler_name = lambda: random.choice(list(HUSTLERS.values())).name
        click.echo()
        click.secho(
            f"(Whenever your input is needed, you can just say what you going to do, "
            f"e.g., \"I want to play with {random_hustler_name()}\", or \"I want to leave the park\").",
            dim=True
        )
        _hint_shown = True

    # Selection loop
    while True:
        user_input = click.prompt("\nYou", prompt_suffix="> ")

        if _is_leaving_park(user_input):
            return None

        await client.query(f"[NARRATOR] {user_input}")
        response = await _get_response(client)
        await _display_response(response, voice_enabled, None)

        # Check if we're approaching someone
        next_action = response.get("next_action", "select_hustler")
        if next_action.startswith("approach_"):
            hustler_id = next_action.replace("approach_", "")
            if hustler_id in HUSTLERS:
                return HUSTLERS[hustler_id]


async def _dialog_phase(client: ClaudeSDKClient, hustler: Hustler, voice_enabled: bool) -> bool:
    """Dialog loop with a specific hustler.

    Returns True if user wants to leave the park entirely, False to go back to park.
    """
    click.echo()
    click.secho(f"--- Talking to {hustler.name} ---", fg="yellow", bold=True)
    click.echo()

    prefix = f"[TALKING TO {hustler.name}]"

    # Initial greeting from the hustler
    await client.query(f"{prefix} Someone just sat down at your table. Greet them.")

    response = await _get_response(client)
    await _display_response(response, voice_enabled, hustler)

    # Dialog loop
    while True:
        user_input = click.prompt("\nYou", prompt_suffix="> ")
        await client.query(f"{prefix} {user_input}")

        response = await _get_response(client)
        await _display_response(response, voice_enabled, hustler)

        intent = response.get("player_intent", "continue")

        if intent == "leaving_park":
            # Hustler detected user wants to leave park - confirm
            user_confirm = click.prompt("\nYou", prompt_suffix="> ")
            await client.query(f"{prefix} {user_confirm}")
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
            await client.query(f"{prefix} {user_confirm}")
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
