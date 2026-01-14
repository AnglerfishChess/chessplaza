"""
Entry point for chessplaza.

Supports running via:
  - uvx chessplaza (after PyPI publish)
  - uv run chessplaza (local development)
  - python -m chessplaza
"""

import click

from chessplaza import __version__


@click.command()
@click.version_option(version=__version__, prog_name="chessplaza")
def main():
    """Welcome to Chess Plaza - play against AI chess hustlers with personality."""
    click.echo(f"Welcome to Chess Plaza v{__version__}")
    click.echo()
    click.echo("The hustlers are setting up their tables...")
    click.echo("Come back soon for a game!")


if __name__ == "__main__":
    main()
