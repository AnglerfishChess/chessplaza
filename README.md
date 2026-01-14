# chessplaza

A virtual chess plaza with AI-powered chess hustlers, each with their own unique personality and playing style.

Think of Washington Square Park in NYC, or Dupont Circle in DC – places where chess hustlers gather to play, banter, and challenge passersby. This project brings that experience to your terminal, powered by LLMs.

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

## Dependencies

- Python 3.10+
- `uv` for package management
- Anthropic API key (for Claude)
- A UCI-compatible chess engine (e.g., Stockfish) via chess-uci-mcp

## Usage

### Via uvx (recommended, after PyPI publish)

```bash
uvx chessplaza
```

### From source

```bash
# Clone the repository
git clone https://github.com/AnglerfishChess/chessplaza.git
cd chessplaza

# Run directly
uv run chessplaza

# Or install in development mode
uv venv --python python3.10
source .venv/bin/activate
uv pip install -e ".[dev]"
chessplaza
```

## Status

v0.0.1 - Project scaffolding. The hustlers are setting up their tables...

## License

MIT License

## Related Projects

- [chess-uci-mcp](https://github.com/AnglerfishChess/chess-uci-mcp) - MCP bridge to UCI chess engines
