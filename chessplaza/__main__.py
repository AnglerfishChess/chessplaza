"""
Entry point for chessplaza.

Supports running via:
  - uvx chessplaza (after PyPI publish)
  - uv run chessplaza (local development)
  - python -m chessplaza
"""

import asyncio

import click
from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

from chessplaza import __version__
from chessplaza.hustler import FAST_EDDIE_PROMPT


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="chessplaza")
@click.pass_context
def main(ctx):
    """Welcome to Chess Plaza - play against AI chess hustlers with personality."""
    if ctx.invoked_subcommand is None:
        click.echo(f"Welcome to Chess Plaza v{__version__}")
        click.echo()
        click.echo("The hustlers are setting up their tables...")
        click.echo("Try: chessplaza talk \"Hey, you any good?\"")


@main.command()
@click.argument("message")
def talk(message: str):
    """Talk to Fast Eddie, the chess hustler."""
    asyncio.run(_talk_to_eddie(message))


async def _talk_to_eddie(message: str):
    """Send a message to Fast Eddie and print his response."""
    options = ClaudeAgentOptions(
        system_prompt=FAST_EDDIE_PROMPT,
        max_turns=1,
        allowed_tools=[],
    )

    async for msg in query(prompt=message, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    click.echo(block.text)


if __name__ == "__main__":
    main()
