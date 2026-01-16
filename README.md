# chessplaza

A virtual chess plaza with AI-powered chess hustlers, each with their own unique personality and playing style.

Think of Washington Square Park in NYC, or Dupont Circle in DC (but not any specific, exact place!) – places where chess hustlers gather to play, banter, and challenge passersby. This project brings that experience to your terminal, powered by LLMs.

## Vision

**Phase 1: Claude Agents SDK Foundation**
- Chess hustler personas powered by Claude Agents SDK
- Integration with UCI chess engines via [chess-uci-mcp](https://github.com/AnglerfishChess/chess-uci-mcp)
- Different hustler personalities: the trash-talker, the philosopher, the speed demon, the old master...

**Phase 2: Multi-AI/SDK Experimentation**
- Support for different AI providers and SDKs
- Compare how different LLMs embody hustler personalities
- Explore agent frameworks and patterns

**Phase 3: Voice Interface**
- Text-to-speech for hustler voices (each with distinct voice characteristics)
- Speech-to-text for calling out your moves
- Full immersive audio experience

## Prerequisites

- **Claude Code** authenticated ([install](https://docs.anthropic.com/en/docs/claude-code/getting-started)), or `ANTHROPIC_API_KEY` env var
- **uv** package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **Stockfish** or another UCI chess engine ([download](https://stockfishchess.org/download/))

## Usage

```bash
# Via uvx (PyPI release)
uvx "chessplaza[voice]" /usr/local/bin/stockfish

# Via uvx (latest from GitHub)
uvx --from "git+https://github.com/AnglerfishChess/chessplaza[voice]" chessplaza /usr/local/bin/stockfish

# From source
git clone https://github.com/AnglerfishChess/chessplaza.git
cd chessplaza
uv run chessplaza /usr/local/bin/stockfish
```

Options (work with any launch method):
- `--voice` / `-v` - enable text-to-speech
- `--language <lang>` / `-l <lang>` - play in a different language (e.g., Spanish, Russian)
- `--use-github-deps` - use bleeding-edge GitHub versions of dependencies (unstable, for development)

### Development setup

```bash
git clone https://github.com/AnglerfishChess/chessplaza.git
cd chessplaza
uv venv --python python3.10
source .venv/bin/activate
uv pip install -e ".[dev,voice]"
chessplaza /usr/local/bin/stockfish
```

## Related Projects

- [chess-uci-mcp](https://github.com/AnglerfishChess/chess-uci-mcp) - MCP bridge to UCI chess engines
