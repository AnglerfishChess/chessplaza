"""
Chat/text game emulator prototype.

Tests rich-as-common-layer approach:
- All output goes through rich Console with markup
- Console mode: rich prints to stdout
- GUI mode: rich records, exports HTML incrementally, appends to widget
"""

import time

import chess
import chess.svg
from rich.console import Console


# Sample chat data for demonstration
SAMPLE_CHAT = [
    ("Eddie", "cyan", "Hey there, welcome to the plaza!"),
    ("Victor", "yellow", "Don't let Eddie fool you. His endgame is weak."),
    ("Eddie", "cyan", "Weak? I beat you three times last week!"),
    ("Mei", "magenta", "Boys, boys... save it for the board."),
]

# Lorem ipsum phrases for stress test
LOREM_PHRASES = [
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco.",
    "Duis aute irure dolor in reprehenderit in voluptate velit.",
    "Excepteur sint occaecat cupidatat non proident.",
    "Sunt in culpa qui officia deserunt mollit anim id est laborum.",
    "Curabitur pretium tincidunt lacus, nulla gravida orci.",
    "Pellentesque habitant morbi tristique senectus et netus.",
    "Vestibulum tortor quam, feugiat vitae, ultricies eget.",
    "Aenean ultricies mi vitae est, mauris sit amet nibh.",
]

SPEAKERS = ["Eddie", "Victor", "Mei", "Marco"]
COLORS = ["cyan", "yellow", "magenta", "green"]


class RichOutput:
    """
    Rich-based output that works for both console and GUI.

    In console mode: prints directly to stdout.
    In GUI mode: records output, exports as HTML, appends to widget.
    """

    def __init__(self, gui_mode: bool = False):
        self.gui_mode = gui_mode

        if gui_mode:
            # Record mode for HTML export
            self.console = Console(record=True, force_terminal=True)
            self._setup_gui()
        else:
            # Normal console output
            self.console = Console()
            self.app = None
            self.chat_display = None

    def _setup_gui(self):
        """Set up PySide6 GUI."""
        try:
            from PySide6.QtWidgets import (
                QApplication,
                QMainWindow,
                QWidget,
                QVBoxLayout,
                QHBoxLayout,
                QTextBrowser,
                QLineEdit,
                QSplitter,
            )
            from PySide6.QtCore import Qt
            from PySide6.QtSvgWidgets import QSvgWidget
            from PySide6.QtGui import QFont
        except ImportError:
            raise ImportError("PySide6 not installed. Install with: uv pip install -e '.[gui]'")

        self.app = QApplication([])
        self.window = QMainWindow()
        self.window.setWindowTitle("Rich-as-Common-Layer Prototype")
        self.window.setMinimumSize(1000, 700)

        central = QWidget()
        main_layout = QHBoxLayout(central)
        splitter = QSplitter(Qt.Horizontal)

        # Chat area
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)

        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(False)
        self.chat_display.setFont(QFont("Menlo", 12))
        self.chat_display.setStyleSheet("""
            QTextBrowser {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
                padding: 10px;
            }
        """)
        self.chat_display.setReadOnly(True)
        chat_layout.addWidget(self.chat_display)

        # Input field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message...")
        self.input_field.setFont(QFont("Menlo", 12))
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #444;
                padding: 8px;
            }
            QLineEdit:disabled {
                background-color: #1a1a1a;
                color: #666;
            }
        """)
        self.input_field.returnPressed.connect(self._on_input_submitted)
        self.input_field.setEnabled(False)
        chat_layout.addWidget(self.input_field)

        splitter.addWidget(chat_container)

        # Chess board
        self.chess_widget = QSvgWidget()
        self.chess_widget.setMinimumSize(400, 400)
        splitter.addWidget(self.chess_widget)

        splitter.setSizes([600, 400])
        main_layout.addWidget(splitter)
        self.window.setCentralWidget(central)

        self._pending_input = None
        self._input_ready = False

    def _on_input_submitted(self):
        """Handle Enter in input field."""
        text = self.input_field.text().strip()
        if text:
            self._pending_input = text
            self._input_ready = True
            self.input_field.clear()
            self.input_field.setEnabled(False)

    def _flush_to_widget(self):
        """Export recorded rich output as HTML and append to widget."""
        if not self.gui_mode or not self.chat_display:
            return

        # Export just the code (spans), not full HTML document
        html = self.console.export_html(clear=True, inline_styles=True, code_format="{code}")

        if html.strip():
            # Convert newlines to <br> for HTML display
            html = html.replace("\n", "<br>")

            # Append and scroll to end
            self.chat_display.insertHtml(html)
            scrollbar = self.chat_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

            # Process events to update display immediately
            self.app.processEvents()

    def print(self, *args, **kwargs):
        """Print using rich, then flush to widget if in GUI mode."""
        self.console.print(*args, **kwargs)
        if self.gui_mode:
            self._flush_to_widget()

    def print_message(self, author: str, color: str, text: str):
        """Print a chat message."""
        self.print(f"[bold {color}]{author}:[/bold {color}] {text}")

    def print_system(self, text: str, bold: bool = False):
        """Print system text."""
        style = "bold dim" if bold else "dim"
        self.print(f"[{style}]{text}[/{style}]")

    def get_input(self, prompt: str = "You") -> str:
        """Get user input."""
        if self.gui_mode:
            self._input_ready = False
            self._pending_input = None
            self.input_field.setEnabled(True)
            self.input_field.setFocus()

            while not self._input_ready:
                self.app.processEvents()
                if not self.window.isVisible():
                    return "quit"

            return self._pending_input or ""
        else:
            return self.console.input(f"[bold green]{prompt}>[/bold green] ")

    def display_chess_position(self, fen: str):
        """Display chess position (GUI only)."""
        if self.gui_mode and self.chess_widget:
            board = chess.Board(fen)
            svg_data = chess.svg.board(board).encode("utf-8")
            self.chess_widget.load(svg_data)


def run_prototype(gui: bool = False) -> None:
    """Run the prototype with rich-as-common-layer."""
    output = RichOutput(gui_mode=gui)

    if gui:
        output.window.show()
        output.display_chess_position(chess.STARTING_FEN)

    # Header
    output.print_system("=== Rich-as-Common-Layer Prototype ===", bold=True)
    output.print("")

    # Initial sample chat
    output.print_system("--- Initial chat messages ---")
    for author, color, text in SAMPLE_CHAT:
        output.print_message(author, color, text)

    output.print("")
    output.print_system("--- Starting lorem ipsum stress test (20 messages with delays) ---")
    output.print("")

    # Lorem ipsum stress test with delays
    for i in range(20):
        speaker = SPEAKERS[i % len(SPEAKERS)]
        color = COLORS[i % len(COLORS)]
        phrase = LOREM_PHRASES[i % len(LOREM_PHRASES)]

        output.print_message(speaker, color, f"[{i + 1}] {phrase}")

        # Small delay to see dynamic behavior
        if gui:
            output.app.processEvents()
        time.sleep(0.15)

    output.print("")
    output.print_system("--- Stress test complete! Now it's your turn ---")
    output.print("")

    # Input loop
    while True:
        if gui and not output.window.isVisible():
            break

        try:
            user_input = output.get_input()
            if user_input.lower() in ("quit", "exit", "q"):
                output.print_system("Goodbye!")
                break
            output.print_message("You", "white", user_input)
        except (KeyboardInterrupt, EOFError):
            output.print_system("\nGoodbye!")
            break


if __name__ == "__main__":
    # GUI mode by default for redistributable .app
    run_prototype(gui=True)
