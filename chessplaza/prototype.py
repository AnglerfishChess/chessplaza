"""
Chat/text game emulator prototype.

Supports both console mode (using rich) and GUI mode (using PySide6).
"""

from abc import ABC, abstractmethod

import chess
import chess.svg

# Rich is always available (core dependency)
from rich.console import Console
from rich.text import Text


# Sample chat data for demonstration
SAMPLE_CHAT = [
    (
        "Eddie",
        "cyan",
        "Hey there, welcome to the plaza! You look like someone who knows their way around a chessboard.",
    ),
    ("Victor", "yellow", "Don't let Eddie fool you. He talks a big game but his endgame is weak."),
    ("Eddie", "cyan", "Weak? I beat you three times last week, old man!"),
    ("Mei", "magenta", "Boys, boys... save the fighting for the board. So, newcomer, you here to play or just watch?"),
    (
        "Marco",
        "green",
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
    ),
    (
        "Eddie",
        "cyan",
        "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
    ),
    (
        "Victor",
        "yellow",
        "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",
    ),
    (
        "Mei",
        "magenta",
        "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
    ),
]


class GameOutput(ABC):
    """Abstract interface for game output - can be console or GUI."""

    @abstractmethod
    def print_message(self, author: str, color: str, text: str) -> None:
        """Print a chat message with colored author name."""
        pass

    @abstractmethod
    def print_system(self, text: str, bold: bool = False) -> None:
        """Print system/narrator text."""
        pass

    @abstractmethod
    def get_input(self, prompt: str = "You") -> str:
        """Get user input."""
        pass

    @abstractmethod
    def run(self) -> None:
        """Run the main loop (blocking for GUI)."""
        pass


class ConsoleOutput(GameOutput):
    """Console implementation using rich library."""

    def __init__(self):
        self.console = Console()

    def print_message(self, author: str, color: str, text: str) -> None:
        styled = Text()
        styled.append(f"{author}: ", style=f"bold {color}")
        styled.append(text)
        self.console.print(styled)

    def print_system(self, text: str, bold: bool = False) -> None:
        style = "bold dim" if bold else "dim"
        self.console.print(text, style=style)

    def get_input(self, prompt: str = "You") -> str:
        return self.console.input(f"[bold green]{prompt}>[/bold green] ")

    def run(self) -> None:
        """Run console chat loop."""
        self.print_system("=== Chat Game Prototype (Console Mode) ===", bold=True)
        self.print_system("")

        # Print sample chat
        for author, color, text in SAMPLE_CHAT:
            self.print_message(author, color, text)

        self.print_system("")
        self.print_system("--- Now it's your turn to chat ---")
        self.print_system("")

        # Input loop
        while True:
            try:
                user_input = self.get_input()
                if user_input.lower() in ("quit", "exit", "q"):
                    self.print_system("Goodbye!")
                    break
                # Echo back
                self.print_message("You", "white", user_input)
            except (KeyboardInterrupt, EOFError):
                self.print_system("\nGoodbye!")
                break


class GUIOutput(GameOutput):
    """GUI implementation using PySide6."""

    def __init__(self):
        # Lazy import PySide6
        try:
            from PySide6.QtWidgets import (
                QApplication,
                QMainWindow,
                QWidget,
                QVBoxLayout,
                QHBoxLayout,
                QTextBrowser,
                QLineEdit,
                QPushButton,
                QSplitter,
            )
            from PySide6.QtCore import Qt, Signal, QObject
            from PySide6.QtSvgWidgets import QSvgWidget
            from PySide6.QtGui import QFont
        except ImportError:
            raise ImportError("PySide6 not installed. Install with: uv pip install -e '.[gui]'")

        self._qt_imports = {
            "QApplication": QApplication,
            "QMainWindow": QMainWindow,
            "QWidget": QWidget,
            "QVBoxLayout": QVBoxLayout,
            "QHBoxLayout": QHBoxLayout,
            "QTextBrowser": QTextBrowser,
            "QLineEdit": QLineEdit,
            "QPushButton": QPushButton,
            "QSplitter": QSplitter,
            "Qt": Qt,
            "Signal": Signal,
            "QObject": QObject,
            "QSvgWidget": QSvgWidget,
            "QFont": QFont,
        }

        self.app = None
        self.window = None
        self.chat_display = None
        self.input_field = None
        self.chess_widget = None
        self._pending_input = None
        self._input_ready = False

    def _setup_ui(self):
        """Set up the GUI components."""
        Qt = self._qt_imports["Qt"]
        QApplication = self._qt_imports["QApplication"]
        QMainWindow = self._qt_imports["QMainWindow"]
        QWidget = self._qt_imports["QWidget"]
        QVBoxLayout = self._qt_imports["QVBoxLayout"]
        QHBoxLayout = self._qt_imports["QHBoxLayout"]
        QTextBrowser = self._qt_imports["QTextBrowser"]
        QLineEdit = self._qt_imports["QLineEdit"]
        QSplitter = self._qt_imports["QSplitter"]
        QSvgWidget = self._qt_imports["QSvgWidget"]
        QFont = self._qt_imports["QFont"]

        self.app = QApplication([])
        self.window = QMainWindow()
        self.window.setWindowTitle("Chat Game Prototype (GUI Mode)")
        self.window.setMinimumSize(1000, 700)

        # Central widget with splitter
        central = QWidget()
        main_layout = QHBoxLayout(central)

        splitter = QSplitter(Qt.Horizontal)

        # Left side: chat area
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)

        # Chat display (HTML-capable)
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
        chat_layout.addWidget(self.chat_display)

        # Input area
        input_layout = QHBoxLayout()
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
        self.input_field.setEnabled(False)  # Initially disabled
        input_layout.addWidget(self.input_field)

        chat_layout.addLayout(input_layout)
        splitter.addWidget(chat_container)

        # Right side: chess board
        self.chess_widget = QSvgWidget()
        self.chess_widget.setMinimumSize(400, 400)
        splitter.addWidget(self.chess_widget)

        splitter.setSizes([600, 400])
        main_layout.addWidget(splitter)

        self.window.setCentralWidget(central)

    def _on_input_submitted(self):
        """Handle Enter pressed in input field."""
        text = self.input_field.text().strip()
        if text:
            self._pending_input = text
            self._input_ready = True
            self.input_field.clear()
            self.input_field.setEnabled(False)

    def print_message(self, author: str, color: str, text: str) -> None:
        """Print a chat message with HTML formatting."""
        # Map color names to HTML colors
        color_map = {
            "cyan": "#00d7ff",
            "yellow": "#ffd700",
            "magenta": "#ff00ff",
            "green": "#00ff00",
            "white": "#ffffff",
            "red": "#ff0000",
            "blue": "#0000ff",
        }
        html_color = color_map.get(color, "#d4d4d4")
        html = f'<span style="color: {html_color}; font-weight: bold;">{author}:</span> {text}<br>'
        self.chat_display.insertHtml(html)
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())

    def print_system(self, text: str, bold: bool = False) -> None:
        """Print system text."""
        weight = "bold" if bold else "normal"
        html = f'<span style="color: #888; font-weight: {weight};">{text}</span><br>'
        self.chat_display.insertHtml(html)
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())

    def get_input(self, prompt: str = "You") -> str:
        """Enable input field and wait for user input."""
        self._input_ready = False
        self._pending_input = None
        self.input_field.setEnabled(True)
        self.input_field.setFocus()

        # Process events until input is ready
        while not self._input_ready:
            self.app.processEvents()
            if not self.window.isVisible():
                return "quit"

        return self._pending_input or ""

    def display_chess_position(self, fen: str) -> None:
        """Display a chess position from FEN string."""
        board = chess.Board(fen)
        svg_data = chess.svg.board(board).encode("utf-8")
        self.chess_widget.load(svg_data)

    def run(self) -> None:
        """Run the GUI application."""
        self._setup_ui()

        self.print_system("=== Chat Game Prototype (GUI Mode) ===", bold=True)
        self.print_system("")

        # Print sample chat
        for author, color, text in SAMPLE_CHAT:
            self.print_message(author, color, text)

        self.print_system("")
        self.print_system("--- Now it's your turn to chat ---")
        self.print_system("")

        # Display initial chess position
        self.display_chess_position(chess.STARTING_FEN)

        self.window.show()

        # Input loop (integrated with Qt event loop)
        while self.window.isVisible():
            user_input = self.get_input()
            if user_input.lower() in ("quit", "exit", "q"):
                self.print_system("Goodbye!")
                break
            # Echo back
            self.print_message("You", "white", user_input)

            # Demo: show a random position after some inputs
            if "move" in user_input.lower() or "chess" in user_input.lower():
                # Show a sample position
                sample_fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
                self.display_chess_position(sample_fen)
                self.print_system("(Chess board updated)")


def run_prototype(gui: bool = False) -> None:
    """Run the chat game prototype.

    Args:
        gui: If True, use PySide6 GUI; otherwise use console with rich.
    """
    if gui:
        output = GUIOutput()
    else:
        output = ConsoleOutput()

    output.run()
