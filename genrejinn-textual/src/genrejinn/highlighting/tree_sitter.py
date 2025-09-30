#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tree-sitter integration for syntax highlighting."""

from pathlib import Path
import sys
import os

# Add the syntax module to the path for backward compatibility
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'syntax'))

try:
    from syntax.manager import tree_sitter_language
    TREE_SITTER_AVAILABLE = tree_sitter_language is not None
except ImportError:
    TREE_SITTER_AVAILABLE = False
    tree_sitter_language = None

from rich.style import Style
from textual.widgets.text_area import TextAreaTheme


class TreeSitterHighlighter:
    """Tree-sitter powered highlighting for multi-color brackets."""

    def __init__(self):
        self.available = TREE_SITTER_AVAILABLE
        self.language = tree_sitter_language.language if TREE_SITTER_AVAILABLE else None
        self.highlight_query = tree_sitter_language.highlight_query if TREE_SITTER_AVAILABLE else None

    def create_akira_theme(self) -> TextAreaTheme:
        """Create Akira-style theme with multi-color highlights."""
        return TextAreaTheme(
            name="akira_highlighted",
            base_style=Style(color="#9aa4ca", bgcolor="#1f1f39"),
            selection_style=Style(color="#1f1f39", bgcolor="#9aa4ca", bold=True),
            cursor_style=Style(color="#ffffff", bgcolor="#9aa4ca"),
            syntax_styles={
                # Yellow highlights (Akira yellow) - [text]
                "highlight.yellow": Style(color="#fbdda7", bold=True),
                "highlight.yellow.content": Style(color="#fbdda7", bold=True),
                "highlight.yellow.bracket": Style(color="#fbdda7", bold=True),

                # Green highlights (Akira green) - {text}
                "highlight.green": Style(color="#6be28d", bold=True),
                "highlight.green.content": Style(color="#6be28d", bold=True),
                "highlight.green.bracket": Style(color="#6be28d", bold=True),

                # Red highlights (Akira red) - <text>
                "highlight.red": Style(color="#ff6a6e", bold=True),
                "highlight.red.content": Style(color="#ff6a6e", bold=True),
                "highlight.red.bracket": Style(color="#ff6a6e", bold=True),

                # Blue highlights (Akira blue) - «text»
                "highlight.blue": Style(color="#b3e3f2", bold=True),
                "highlight.blue.content": Style(color="#b3e3f2", bold=True),
                "highlight.blue.bracket": Style(color="#b3e3f2", bold=True),

                # White highlights (Akira white) - ⟨text⟩
                "highlight.white": Style(color="#ffffff", bold=True),
                "highlight.white.content": Style(color="#ffffff", bold=True),
                "highlight.white.bracket": Style(color="#ffffff", bold=True),
            }
        )

    def register_with_textarea(self, text_area) -> bool:
        """Register the custom language and theme with a TextArea widget."""
        if not self.available:
            return False

        try:
            # Register our custom tree-sitter language with TextArea
            text_area.register_language(
                "custom",
                self.language,
                self.highlight_query
            )

            # Register and apply the theme
            theme = self.create_akira_theme()
            text_area.register_theme(theme)
            text_area.theme = "akira_highlighted"
            text_area.language = "custom"

            return True
        except Exception as e:
            print(f"Failed to register tree-sitter language: {e}")
            return False