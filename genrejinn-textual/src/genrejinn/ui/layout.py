#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Main layout components for GenreJinn UI."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static, TextArea, ProgressBar, ListView, Input


class MainLayout:
    """Main layout container for the GenreJinn application."""

    def __init__(self, app):
        self.app = app

    def create_left_panel(self, pages: list, tree_sitter_highlighter) -> ComposeResult:
        """Create the left panel with text area and controls."""
        with Vertical(id="left-panel"):
            # Main text area
            text_area = TextArea(
                pages[0] if pages else "No content",
                id="text-area",
                read_only=False
            )

            # Try to register tree-sitter language
            if tree_sitter_highlighter and tree_sitter_highlighter.register_with_textarea(text_area):
                pass  # Tree-sitter registered successfully
            else:
                print("Using fallback highlighting")

            yield text_area

            # Controls section
            with Vertical(id="left-controls"):
                yield Static(f"1 / {len(pages)}", id="counter")

                # Navigation controls
                with Horizontal():
                    back_button = Button("Back", id="prev")
                    back_button.can_focus = False
                    back_button.active_effect_duration = 0
                    yield back_button

                    yield ProgressBar(
                        total=len(pages),
                        show_percentage=False,
                        show_eta=False,
                        id="progress"
                    )

                    next_button = Button("Next", id="next")
                    next_button.can_focus = False
                    next_button.active_effect_duration = 0
                    yield next_button

                # Highlight controls
                with Horizontal(id="highlight-controls"):
                    mark_button = Button("Mark", id="mark")
                    mark_button.can_focus = False
                    mark_button.active_effect_duration = 0
                    mark_button.styles.color = "#ffffff"
                    yield mark_button

                    # Color cycling button
                    color_button = Button("YEL", id="color-button")
                    color_button.can_focus = False
                    color_button.active_effect_duration = 0
                    color_button.styles.color = "#fbdda7"
                    yield color_button

                    highlight_button = Button("Highlight", id="highlight")
                    highlight_button.can_focus = False
                    highlight_button.active_effect_duration = 0
                    yield highlight_button

                    save_button = Button("Save", id="save-note")
                    save_button.can_focus = False
                    save_button.active_effect_duration = 0
                    yield save_button

                    delete_button = Button("Delete", id="delete-highlight")
                    delete_button.can_focus = False
                    delete_button.active_effect_duration = 0
                    yield delete_button

                # Search controls
                with Horizontal(id="search-controls"):
                    search_input = Input(placeholder="Search...", id="search-input")
                    search_input.can_focus = True
                    yield search_input

                    prev_search_button = Button("<", id="prev-search")
                    prev_search_button.can_focus = False
                    prev_search_button.active_effect_duration = 0
                    yield prev_search_button

                    next_search_button = Button(">", id="next-search")
                    next_search_button.can_focus = False
                    next_search_button.active_effect_duration = 0
                    yield next_search_button

    def create_right_panel(self) -> ComposeResult:
        """Create the right panel with notes and highlights."""
        with Vertical(id="notes-panel"):
            yield Static("HIGHLIGHTS & NOTES", id="notes-title")

            # Mark input field (initially hidden)
            mark_input = Input(placeholder="Enter mark name...", id="mark-input")
            mark_input.styles.display = "none"
            yield mark_input

            # Highlights list
            highlights_list = ListView(id="highlights-list")
            highlights_list.styles.background = "#1f1f39"
            highlights_list.can_focus = False
            yield highlights_list