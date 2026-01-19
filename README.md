# chessplaza

A virtual chess plaza with AI-powered chess hustlers, each with their own unique personality and playing style.

Think of Washington Square Park in NYC, or Dupont Circle in DC (but not any specific, exact place!) – places where chess hustlers gather to play, banter, and challenge passersby. This project brings that experience to your terminal, powered by LLMs.

## Roadmap

**Phase 1: Claude Agents epoch**
- Chess hustler personas powered by Claude Agents SDK;
- Integration with UCI chess engines via [chess-uci-mcp](https://github.com/AnglerfishChess/chess-uci-mcp);
- Different hustler personalities: the trash-talker, the philosopher, the speed demon, the old master...
- Game/chat loop using Claude Agents SDK.

**Phase 2: Experimentation epoch**
- Basic voice output (Edge-TTS), complementing the text UI;
- Voice input (Whisper) to call out your moves (and words) instead of keyboard input;
- Switchable UI: command-line vs PySide-based (with proper chess board).

**Phase 3: LangGraph/Gemini epoch**
- Switching to Gemini, for LLM but specifically for advanced text-to-speech (each with distinct voice characteristics, intonations, etc);
- (Because of Gemini switch) Migrating from Claude Agents SDK to `GenAI` SDK (TTS, one-shot queries) and LangGraph (game/chat loop).

## Prerequisites

- **Claude Code** authenticated ([install](https://docs.anthropic.com/en/docs/claude-code/getting-started)), or `ANTHROPIC_API_KEY` environment variable;
- **uv** package manager ([install](https://docs.astral.sh/uv/getting-started/installation/));
- **Stockfish** or another UCI chess engine ([download](https://stockfishchess.org/download/)).

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

### Building Redistributables

PyInstaller is included in dev dependencies for building standalone apps. Full build instructions coming soon.

## Troubleshooting

### macOS: Microphone not working (voice input)

If voice input records silence or doesn't work, your terminal app likely lacks microphone permissions.

**Fix:**
1. Open **System Settings → Privacy & Security → Microphone**
2. Find your terminal app (Terminal, iTerm2, VS Code, etc.) and enable it
3. If not listed, the app hasn't requested access yet – try restarting the app

**Verify via command line:**
```bash
# Check which apps have microphone access
tccutil list Microphone
```

**Still not working?** Reset permissions to trigger a fresh prompt:
```bash
# For Terminal.app
tccutil reset Microphone com.apple.Terminal

# For iTerm2
tccutil reset Microphone com.googlecode.iterm2
```

## Related Projects

- [chess-uci-mcp](https://github.com/AnglerfishChess/chess-uci-mcp) - MCP bridge to UCI chess engines
