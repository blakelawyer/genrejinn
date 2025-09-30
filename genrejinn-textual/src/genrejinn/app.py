#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Main GenreJinn EPUB Reader application using modular architecture."""

import sys
import os
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static, TextArea, ProgressBar, ListView, ListItem, Label, Input, Markdown
from textual.screen import ModalScreen
from textual.reactive import reactive
from textual.events import Click
import webbrowser

# Import all the modular components
from .epub import EPUBParser, EPUBPaginator
from .highlighting import HighlightManager, ColorManager, TreeSitterHighlighter
from .ui import ClickableImage, AkiraTheme, MainLayout
from .storage import HighlightStorage, MarkStorage, ImageManager, PageStateManager
from .utils import SearchEngine, ServerManager, debug_log

# Try to import tree-sitter language from syntax module
try:
    from syntax.manager import tree_sitter_language
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    debug_log("Tree-sitter syntax module not available")


class EPUBReader(App):
    """Main EPUB Reader application with modular architecture."""

    # Use AkiraTheme for styling
    CSS = AkiraTheme.get_main_css()

    # Reactive attributes for state management
    current_page = reactive(0)

    def __init__(self):
        """Initialize the EPUB Reader with all modular components."""
        super().__init__()

        # Initialize core modules
        self.epub_parser = EPUBParser()
        self.epub_paginator = EPUBPaginator()
        self.highlight_manager = HighlightManager()
        self.color_manager = ColorManager()
        self.tree_sitter_highlighter = TreeSitterHighlighter()

        # Initialize storage modules
        self.highlight_storage = HighlightStorage()
        self.mark_storage = MarkStorage()
        self.image_manager = ImageManager()
        self.page_state_manager = PageStateManager()

        # Initialize utility modules
        self.search_engine = SearchEngine()
        self.server_manager = ServerManager()

        # Load EPUB content and restore state
        self.pages = self._load_epub_content()
        self.highlight_manager.highlights = self.highlight_storage.load_highlights()
        self.marks = self.mark_storage.load_marks()

        # Restore page state
        self.saved_page_to_load = self.page_state_manager.load_current_page(len(self.pages))

        # UI state tracking
        self.last_focused_textarea = None
        self.last_clicked_mark = None
        self.last_interaction_type = None
        self.mark_dropdown_states = {}

        # Color cycling for highlight button
        self.current_color_index = 0
        self.highlight_colors = self.color_manager.get_highlight_colors()

        # Button feedback state tracking
        self.button_feedback_active = {}

        # Pending mark creation state
        self._pending_mark = None

        debug_log("EPUBReader initialized with modular architecture")

    def _load_epub_content(self) -> list:
        """Load EPUB content using the EPUBParser module."""
        try:
            # Look for EPUB files in the current directory
            epub_files = list(Path(".").glob("*.epub"))
            if not epub_files:
                debug_log("No EPUB files found in current directory")
                return ["No EPUB files found. Please place an EPUB file in the current directory."]

            # Use the first EPUB file found
            epub_file = epub_files[0]
            debug_log(f"Loading EPUB file: {epub_file}")

            # Parse EPUB content
            self.epub_parser.epub_path = str(epub_file)
            paragraphs = self.epub_parser.load_paragraphs()
            if not paragraphs:
                debug_log("Failed to parse EPUB content")
                return ["Failed to parse EPUB content."]

            # Paginate content
            pages = self.epub_paginator.create_pages(paragraphs)
            debug_log(f"Successfully loaded {len(pages)} pages")
            return pages

        except Exception as e:
            debug_log(f"Error loading EPUB content: {e}")
            return [f"Error loading EPUB: {str(e)}"]

    def compose(self) -> ComposeResult:
        """Compose the main UI layout using the MainLayout module."""
        layout = MainLayout()

        # Create main content area with text
        text_area = TextArea(
            self.pages[0] if self.pages else "No content",
            id="text-area",
            read_only=False
        )

        # Register tree-sitter language if available
        if TREE_SITTER_AVAILABLE:
            try:
                self.tree_sitter_highlighter.register_language(text_area)
                debug_log("Tree-sitter language registered successfully")
            except Exception as e:
                debug_log(f"Failed to register tree-sitter language: {e}")

        # Yield the complete layout
        yield from layout.create_layout(
            text_area=text_area,
            total_pages=len(self.pages),
            highlight_colors=self.highlight_colors,
            current_color_index=self.current_color_index
        )

    def on_mount(self) -> None:
        """Called when the app is mounted and ready."""
        # Set the current page from saved state
        if hasattr(self, 'saved_page_to_load'):
            self.current_page = self.saved_page_to_load
            debug_log(f"Restored current page to: {self.current_page}")

        # Apply highlighting if highlights exist
        if self.highlights:
            self._apply_highlights()

        # Update the highlights list
        self._update_highlights_list()

        # Schedule periodic state saving
        self.set_interval(30.0, self._save_current_state)

        debug_log("EPUBReader mounted successfully")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        debug_log(f"Button pressed: {button_id}")

        if button_id == "next":
            self._navigate_next()
        elif button_id == "prev":
            self._navigate_prev()
        elif button_id == "highlight":
            self._toggle_highlight()
        elif button_id == "save":
            self._save_note()
        elif button_id == "delete":
            self._delete_item()
        elif button_id == "search":
            self._open_search()
        elif button_id.startswith("mark-"):
            self._handle_mark_button(button_id)

    def _navigate_next(self) -> None:
        """Navigate to the next page."""
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self._update_page_display()
            debug_log(f"Navigated to page {self.current_page + 1}")

    def _navigate_prev(self) -> None:
        """Navigate to the previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_page_display()
            debug_log(f"Navigated to page {self.current_page + 1}")

    def _update_page_display(self) -> None:
        """Update the text area and UI elements for the current page."""
        text_area = self.query_one("#text-area", TextArea)
        text_area.text = self.pages[self.current_page]

        # Update counter and progress bar
        counter = self.query_one("#counter", Static)
        counter.update(f"{self.current_page + 1} / {len(self.pages)}")

        progress_bar = self.query_one("#progress", ProgressBar)
        progress_bar.update(progress=self.current_page + 1)

        # Apply highlights for current page
        self._apply_highlights()

        # Update highlights list
        self._update_highlights_list()

    def _toggle_highlight(self) -> None:
        """Toggle highlighting using the HighlightManager."""
        text_area = self.query_one("#text-area", TextArea)

        if text_area.selected_text:
            # Get current color
            color_name, color_code = self.highlight_colors[self.current_color_index]

            # Use highlight manager to create highlight
            highlight = self.highlight_manager.create_highlight(
                text=text_area.selected_text,
                page=self.current_page,
                position=text_area.selection,
                color=color_name.lower()
            )

            if highlight:
                # Store highlight
                if self.current_page not in self.highlights:
                    self.highlights[self.current_page] = []
                self.highlights[self.current_page].append(highlight)

                # Save to storage
                self.highlight_storage.save_highlights(self.highlights)

                # Apply visual highlighting
                self._apply_highlights()
                self._update_highlights_list()

                debug_log(f"Created highlight: {highlight}")

            # Cycle to next color
            self.current_color_index = (self.current_color_index + 1) % len(self.highlight_colors)
            self._update_highlight_button()

    def _save_note(self) -> None:
        """Save note using the last focused textarea."""
        if self.last_focused_textarea and self.last_interaction_type == 'note':
            note_text = self.last_focused_textarea.text
            # Logic to save the note would go here
            debug_log(f"Saving note: {note_text}")

    def _delete_item(self) -> None:
        """Delete the last interacted item (highlight or mark)."""
        if self.last_interaction_type == 'note' and self.last_focused_textarea:
            # Logic to delete highlight associated with this note
            debug_log("Deleting highlight")
        elif self.last_interaction_type == 'mark' and self.last_clicked_mark:
            # Logic to delete mark
            debug_log("Deleting mark")

    def _open_search(self) -> None:
        """Open search interface using SearchEngine."""
        # This would typically push a search screen
        debug_log("Opening search interface")

    def _handle_mark_button(self, button_id: str) -> None:
        """Handle mark button interactions."""
        mark_id = button_id.replace("mark-", "")
        debug_log(f"Mark button clicked: {mark_id}")

    def _apply_highlights(self) -> None:
        """Apply highlights to the current page using TreeSitterHighlighter."""
        if self.current_page in self.highlights:
            text_area = self.query_one("#text-area", TextArea)
            page_highlights = self.highlights[self.current_page]

            # Use tree-sitter highlighter to apply highlights
            self.tree_sitter_highlighter.apply_highlights(text_area, page_highlights)

    def _update_highlights_list(self) -> None:
        """Update the highlights list view."""
        highlights_list = self.query_one("#highlights-list", ListView)
        highlights_list.clear()

        # Add highlights for current page
        if self.current_page in self.highlights:
            for highlight in self.highlights[self.current_page]:
                item = ListItem(Label(highlight.get('text', 'Unknown highlight')))
                highlights_list.append(item)

    def _update_highlight_button(self) -> None:
        """Update the highlight button to show current color."""
        color_name, color_code = self.highlight_colors[self.current_color_index]
        highlight_button = self.query_one("#highlight-button", Button)
        highlight_button.label = f"Highlight ({color_name})"

    def _save_current_state(self) -> None:
        """Save current application state."""
        self.page_state_manager.save_current_page(self.current_page)

    def on_unmount(self) -> None:
        """Save state when app is closing."""
        self._save_current_state()
        self.highlight_storage.save_highlights(self.highlights)
        self.mark_storage.save_marks(self.marks)
        debug_log("EPUBReader unmounted and state saved")


# Export the main class
__all__ = ["EPUBReader"]