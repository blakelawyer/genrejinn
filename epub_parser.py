#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zipfile
import re
import pickle
import os
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Center, Middle
from textual.screen import Screen
from textual.widgets import Button, Static, TextArea, ProgressBar, ListView, ListItem, Label, OptionList, Input
from textual.widgets.text_area import TextAreaTheme
from rich.style import Style
from textual.reactive import reactive
from syntax.manager import tree_sitter_language
# Debug logging function
def debug_log(message):
    with open('log.txt', 'a') as f:
        f.write(f"{message}\n")
        f.flush()

# Color management system

class ColorManager:
    """Centralized color management for highlights"""
    
    # 3-character codes to full color names
    COLOR_MAPPING = {
        "yel": "yellow",
        "red": "red", 
        "grn": "green",
        "blu": "blue",
        "wht": "white"
    }
    
    # Color brackets for text wrapping
    COLOR_BRACKETS = {
        "yellow": ("[", "]"),
        "green": ("{", "}"),
        "red": ("<", ">"),
        "blue": ("«", "»"),
        "white": ("⟨", "⟩")
    }
    
    # Color hex values for display
    COLOR_HEX = {
        "yellow": "#fbdda7",
        "red": "#ff6a6e",
        "green": "#6be28d", 
        "blue": "#b3e3f2",
        "white": "#ffffff"
    }
    
    @classmethod
    def get_full_color_name(cls, short_name: str) -> str:
        """Convert 3-char code to full color name"""
        return cls.COLOR_MAPPING.get(short_name.lower(), "yellow")
    
    @classmethod
    def get_brackets(cls, color: str) -> tuple:
        """Get open/close brackets for a color"""
        return cls.COLOR_BRACKETS.get(color, ("[", "]"))
    
    @classmethod
    def get_hex(cls, color: str) -> str:
        """Get hex value for a color"""
        return cls.COLOR_HEX.get(color, "#fbdda7")
    
    @classmethod
    def strip_brackets(cls, text: str, color: str) -> str:
        """Strip bracket characters from highlighted text to get clean content."""
        if not text or color not in cls.COLOR_BRACKETS:
            return text
        
        open_bracket, close_bracket = cls.COLOR_BRACKETS[color]
        
        # Remove opening bracket if text starts with it
        if text.startswith(open_bracket):
            text = text[len(open_bracket):]
        
        # Remove closing bracket if text ends with it
        if text.endswith(close_bracket):
            text = text[:-len(close_bracket)]
        
        return text
    
    @classmethod
    def wrap_text_with_color(cls, text: str, color: str) -> str:
        """Wrap text with color brackets"""
        open_bracket, close_bracket = cls.get_brackets(color)
        return f"{open_bracket}{text}{close_bracket}"

def parse_highlight_tuple(highlight: tuple) -> tuple:
    """Parse highlight tuple handling both old (4-element) and new (5-element) formats.
    
    Returns: (start_pos, end_pos, text, note, color)
    """
    if len(highlight) == 4:
        start_pos, end_pos, text, note = highlight
        return start_pos, end_pos, text, note, "yellow"
    else:
        return highlight  # Already 5 elements



class EPUBReader(App):
    CSS = """
    Screen {
        background: #1f1f39;
    }
    
    #main-content {
        height: 100vh;
    }
    
    #left-panel {
        width: 60%;
    }
    
    
    TextArea {
        background: #1f1f39;
        color: #9aa4ca;
        margin: 1;
        padding: 1;
        border: solid #9aa4ca;
    }
    
    
    #left-controls {
        height: auto;
        min-height: 5;
        background: #1f1f39;
        border: solid #9aa4ca;
        margin: 0 1 1 1;
        padding: 1;
        min-width: 0;
    }
    
    #notes-panel {
        margin: 1;
        padding: 1;
        border: solid #9aa4ca;
        background: #1f1f39;
        color: #ffffff;
        width: 40%;
        height: 100%;
    }
    
    #notes-title {
        text-align: center;
        color: #9aa4ca;
        background: #1f1f39;
        margin-bottom: 1;
    }
    
    #highlights-list {
        background: #1f1f39;
        color: #ffffff;
        height: 1fr;
    }
    
    ListView {
        background: #1f1f39;
    }
    
    ListItem {
        background: #1f1f39;
        color: #ffffff;
        padding: 1;
        margin: 0 0 1 0;
        border: solid #9aa4ca 50%;
        height: auto;
    }
    
    ListItem:hover {
        background: #2f2f49;
    }
    
    ListItem > Label {
        color: #ffffff;
        background: transparent;
        text-wrap: wrap;
        width: 100%;
        height: auto;
    }
    
    #note-input {
        background: #2f2f49;
        color: #9aa4ca;
        border: solid #9aa4ca;
        margin: 1 0;
        padding: 1;
        height: 5;
        visibility: hidden;
    }
    
    .hidden {
        display: none;
    }
    
    Button {
        min-width: 4;
        margin: 0 1;
        background: #1f1f39;
        border: solid #9aa4ca;
        color: #9aa4ca;
    }
    
    #text-area {
        height: 1fr;
    }
    
    #left-controls {
        height: auto;
        align: center middle;
    }
    
    #left-controls > Horizontal {
        width: 100%;
        align: center middle;
        margin-bottom: 1;
        height: auto;
    }
    
    #progress {
        width: auto;
        min-width: 0;
        margin: 1 1 0 1;
        text-align: center;
    }
    
    #prev, #next {
        width: auto;
        min-width: 4;
        max-width: 8;
    }
    
    #counter {
        text-align: center;
        margin: 0;
        color: #ffffff !important;
    }
    
    Static#counter {
        color: #ffffff !important;
    }
    
    /* Button text colors */
    #highlight {
        color: #b3e3f2;
    }
    
    #save-note {
        color: #6be28d;
    }
    
    #delete-highlight {
        color: #ff6a6e;
    }
    
    #prev, #next {
        color: #fbdda7;
    }
    
    #color-button {
        color: #9aa4ca;
        min-width: 11;
        text-align: center;
    }
    
    #color-button:focus {
        background: #1f1f39 !important;
        border: solid #9aa4ca !important;
        outline: none !important;
    }
    
    #color-button:hover {
        background: #1f1f39;
    }
    
    #prev:focus, #next:focus, #highlight:focus, #save-note:focus, #delete-highlight:focus {
        background: #1f1f39 !important;
        border: solid #9aa4ca !important;
        outline: none !important;
    }
    
    #prev:hover, #next:hover, #highlight:hover, #save-note:hover, #delete-highlight:hover {
        background: #1f1f39;
    }
    
    
    #highlight-controls {
        height: auto;
        align: center middle;
    }
    
    #counter {
        text-align: center;
        width: 1fr;
        color: #9aa4ca;
        background: #1f1f39;
    }
    
    #notes-title {
        color: #ffffff;
        text-style: bold;
    }
    
    
    ProgressBar {
        background: #1f1f39;
        color: #9aa4ca;
    }
    
    /* Style the actual Bar widget inside ProgressBar */
    Bar > .bar--bar {
        color: #6be28d;
        background: #ff6a6e;
    }
    
    Bar > .bar--complete {
        color: #fbdda7;
        background: #ff6a6e;
    }
    
    /* TextArea inside ListView items */
    ListView ListItem TextArea {
        height: auto;
        min-height: 3;
        border: none;
        margin: 0;
        padding: 1;
        background: #1f1f39;
        color: #9aa4ca;
        overflow-y: hidden;
    }
    
    /* Ensure ListView items have proper sizing */
    ListView ListItem {
        height: auto;
        min-height: 5;
        padding: 1;
    }
    
    /* Disable hover highlighting on ListView items */
    ListView ListItem:hover {
        background: #1f1f39;
    }
    
    /* Disable highlighting on ListView container and selection */
    ListView {
        background: #1f1f39 !important;
    }
    
    ListView:focus {
        background: #1f1f39 !important;
    }
    
    /* Target the specific highlights-list with multiple selectors */
    #highlights-list {
        background: #1f1f39 !important;
    }
    
    #highlights-list:focus {
        background: #1f1f39 !important;
    }
    
    /* Try to override any ListView internal styling */
    ListView#highlights-list {
        background: #1f1f39 !important;
    }
    
    /* Target the highlight class that's being applied */
    ListView.-highlight {
        background: #1f1f39 !important;
    }
    
    #highlights-list.-highlight {
        background: #1f1f39 !important;
    }
    
    /* Also target hovered state */
    ListView.-hovered {
        background: #1f1f39 !important;
    }
    
    #highlights-list.-hovered {
        background: #1f1f39 !important;
    }
    
    /* Disable ListView selection highlighting */
    ListView > .datatable--cursor {
        background: transparent;
    }
    
    ListView ListItem.--highlight {
        background: #1f1f39;
    }
    
    ListView ListItem:focus {
        background: #1f1f39;
    }
    
    /* Override any possible selection states */
    ListView ListItem.--selected {
        background: #1f1f39 !important;
    }
    
    ListView ListItem.-selected {
        background: #1f1f39 !important;
    }
    
    ListView ListItem Vertical {
        height: auto;
    }
    
    /* Scrollbar styling using correct Textual properties */
    TextArea {
        scrollbar-background: #1f1f39;
        scrollbar-background-active: #1f1f39;
        scrollbar-background-hover: #1f1f39;
        scrollbar-color: #9aa4ca;
        scrollbar-color-active: #9aa4ca;
        scrollbar-color-hover: #9aa4ca;
        scrollbar-corner-color: #1f1f39;
    }
    
    ListView {
        scrollbar-background: #1f1f39;
        scrollbar-background-active: #1f1f39;
        scrollbar-background-hover: #1f1f39;
        scrollbar-color: #9aa4ca;
        scrollbar-color-active: #9aa4ca;
        scrollbar-color-hover: #9aa4ca;
        scrollbar-corner-color: #1f1f39;
    }
    
    /* Apply to all widgets with scrollbars */
    * {
        scrollbar-background: #1f1f39;
        scrollbar-background-active: #1f1f39;
        scrollbar-background-hover: #1f1f39;
        scrollbar-color: #9aa4ca;
        scrollbar-color-active: #9aa4ca;
        scrollbar-color-hover: #9aa4ca;
        scrollbar-corner-color: #1f1f39;
    }
    
    /* Mark input field styling */
    #mark-input {
        background: #1f1f39;
        color: #9aa4ca;
        border: solid #9aa4ca;
        margin-bottom: 1;
    }
    
    """
    
    current_page = reactive(0)
    
    def __init__(self):
        super().__init__()
        self.pages = self._load_epub_content()
        # Store highlights as {page_number: [(start_pos, end_pos, text, note, color), ...]}
        self.highlights = {}
        self.last_focused_textarea = None  # Track the last focused TextArea for save/delete operations
        # Color cycling for highlight button
        self.current_color_index = 0
        self.highlight_colors = [
            ("YEL", "#fbdda7"),
            ("RED", "#ff6a6e"), 
            ("GRN", "#6be28d"),
            ("BLU", "#b3e3f2"),
            ("WHT", "#ffffff")
        ]
        # Button feedback state tracking
        self.button_feedback_active = {}
        # Marks for organizing highlights into sections
        self.marks = []  # List of (page_num, start_row, start_col, mark_text, mark_name, timestamp)
        # Load existing highlights
        self.load_highlights()
    
    def _load_epub_paragraphs(self, epub_path: str = 'bookshelf/gravitys-rainbow.epub') -> list:
        """Load paragraphs from EPUB file."""
        debug_log("Starting EPUB loading...")
        
        with zipfile.ZipFile(epub_path, 'r') as epub_file:
            html_files = [f for f in epub_file.namelist() if f.endswith('.html') and 'text' in f]
            html_files.sort()
            
            all_paragraphs = []
            for filename in html_files:
                content = epub_file.read(filename).decode('utf-8', errors='ignore')
                para_matches = re.findall(r'<p[^>]*>(.*?)</p>', content, re.DOTALL | re.IGNORECASE)
                
                for para_html in para_matches:
                    para_text = re.sub(r'<[^>]+>', '', para_html)
                    para_text = re.sub(r'\s+', ' ', para_text).strip()
                    
                    if para_text:
                        all_paragraphs.append(para_text)
        
        debug_log(f"Loaded {len(all_paragraphs)} paragraphs total")
        return all_paragraphs
    
    def _create_pages(self, paragraphs: list, total_pages: int = 776) -> list:
        """Group paragraphs into pages."""
        if not paragraphs:
            return []
        
        pages = []
        total_paragraphs = len(paragraphs)
        paragraphs_per_page = total_paragraphs // total_pages
        extra_paragraphs = total_paragraphs % total_pages
        
        start_index = 0
        for page_num in range(total_pages):
            # Some pages get one extra paragraph to distribute the remainder
            page_size = paragraphs_per_page + (1 if page_num < extra_paragraphs else 0)
            
            if start_index >= total_paragraphs:
                # If we run out of paragraphs, create empty pages
                pages.append("")
            else:
                end_index = min(start_index + page_size, total_paragraphs)
                page_paragraphs = paragraphs[start_index:end_index]
                pages.append('\n\n'.join(page_paragraphs))
                start_index = end_index
        
        return pages
    
    def _load_epub_content(self) -> list:
        """Load and process EPUB content into pages."""
        paragraphs = self._load_epub_paragraphs()
        pages = self._create_pages(paragraphs)
        debug_log(f"Created {len(pages)} pages from paragraphs")
        return pages
    
    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="main-content"):
                with Vertical(id="left-panel"):
                    text_area = TextArea(self.pages[0] if self.pages else "No content", id="text-area", read_only=False)
                    
                    # Register our custom tree-sitter language with TextArea
                    try:
                        text_area.register_language(
                            "custom",
                            tree_sitter_language.language,
                            tree_sitter_language.highlight_query
                        )
                        language_registered = True
                    except Exception as e:
                        debug_log(f"Failed to register language: {e}")
                        language_registered = False
                    
                    # Create Akira-style theme with multi-color highlights
                    highlight_theme = TextAreaTheme(
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
                        }
                    )
                    
                    text_area.register_theme(highlight_theme)
                    text_area.theme = "akira_highlighted"
                    
                    # Set the language to use our custom parser
                    if language_registered:
                        text_area.language = "custom"
                    else:
                        debug_log("Using fallback highlighting")
                    
                    yield text_area
                    with Vertical(id="left-controls"):
                        yield Static(f"1 / {len(self.pages)}", id="counter")
                        with Horizontal():
                            back_button = Button("Back", id="prev")
                            back_button.can_focus = False
                            back_button.active_effect_duration = 0
                            yield back_button
                            yield ProgressBar(total=len(self.pages), show_percentage=False, show_eta=False, id="progress")
                            next_button = Button("Next", id="next")
                            next_button.can_focus = False
                            next_button.active_effect_duration = 0
                            yield next_button
                        with Horizontal(id="highlight-controls"):
                            # Mark button for creating section markers
                            mark_button = Button("Mark", id="mark")
                            mark_button.can_focus = False
                            mark_button.active_effect_duration = 0
                            mark_button.styles.color = "#ffffff"
                            yield mark_button
                            
                            # Set up color button with initial yellow color
                            color_name, color_hex = self.highlight_colors[self.current_color_index]
                            color_button = Button(color_name, id="color-button")
                            color_button.can_focus = False
                            color_button.active_effect_duration = 0
                            color_button.styles.color = color_hex
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
                with Vertical(id="notes-panel"):
                    yield Static("HIGHLIGHTS & NOTES", id="notes-title")
                    
                    # Mark input field (initially hidden)
                    mark_input = Input(placeholder="Enter mark name...", id="mark-input")
                    mark_input.styles.display = "none"
                    yield mark_input
                    
                    
                    # Add test mark dropdown
                    test_mark_button = Button("TEST MARK ▼", id="test-mark-dropdown")
                    test_mark_button.can_focus = False
                    test_mark_button.active_effect_duration = 0
                    test_mark_button.styles.color = "#ffffff"
                    test_mark_button.styles.width = "100%"
                    test_mark_button.styles.text_align = "left"
                    yield test_mark_button
                    
                    highlights_list = ListView(id="highlights-list")
                    highlights_list.styles.background = "#1f1f39"
                    # Disable ListView's built-in selection behavior
                    highlights_list.can_focus = False
                    yield highlights_list
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Add visual feedback to all buttons
        self._add_button_press_feedback(event.button)
        
        if event.button.id == "next" and self.current_page < len(self.pages) - 1:
            self.current_page += 1
        elif event.button.id == "prev" and self.current_page > 0:
            self.current_page -= 1
        elif event.button.id == "mark":
            self.create_simple_mark()
        elif event.button.id == "highlight":
            self.highlight_selected_text()
        elif event.button.id == "save-note":
            # Check if we have a pending mark to save, otherwise save focused note
            if hasattr(self, '_pending_mark'):
                self.save_pending_mark()
            else:
                self.save_focused_note()
        elif event.button.id == "delete-highlight":
            self.delete_focused_highlight()
        elif event.button.id == "color-button":
            self.cycle_color()
        elif event.button.id == "test-mark-dropdown":
            self.toggle_test_mark_dropdown()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input fields."""
        if event.input.id == "mark-input":
            # Enter key saves the mark
            self.save_pending_mark()
    
    
    def _add_button_press_feedback(self, button: Button) -> None:
        """Add visual feedback when button is pressed by changing border and text color briefly."""
        button_id = button.id
        
        # If feedback is already active for this button, ignore the new click
        if self.button_feedback_active.get(button_id, False):
            return
        
        # Mark feedback as active
        self.button_feedback_active[button_id] = True
        
        # Store original styles (only if not already stored)
        if not hasattr(button, '_original_border'):
            button._original_border = button.styles.border
            button._original_outline = button.styles.outline
            button._original_color = button.styles.color
        
        # Change border to heavy style with foreground color
        button.styles.border = ("heavy", "#9aa4ca")
        
        # Only change text color for non-color buttons to preserve color button's intended color
        if button_id != "color-button":
            button.styles.color = "#9aa4ca"  # Text color becomes foreground color
        
        # Revert styles after brief delay
        self.set_timer(0.5, lambda: self._revert_button_styles(button))
    
    def _revert_button_styles(self, button: Button) -> None:
        """Revert button styles to original state."""
        button_id = button.id
        
        # Restore original styles
        if hasattr(button, '_original_border'):
            button.styles.border = button._original_border
            button.styles.outline = button._original_outline
            
            # For color button, don't restore the stored color - use current color from highlight_colors
            if button_id == "color-button":
                color_name, color_hex = self.highlight_colors[self.current_color_index]
                button.styles.color = color_hex
            else:
                button.styles.color = button._original_color
        
        # Mark feedback as inactive
        self.button_feedback_active[button_id] = False
    
    
    def create_simple_mark(self) -> None:
        """Start mark creation by showing input field."""
        text_area = self.query_one("#text-area", TextArea)
        
        if text_area.selection.is_empty:
            debug_log("No text selected for mark")
            return
        
        # Get the selected text and position
        selected_text = text_area.selected_text.strip()
        if not selected_text:
            debug_log("Empty text selected for mark")
            return
        
        # Get cursor position and store as pending mark
        start_row, start_col = text_area.selection.start
        self._pending_mark = (self.current_page, start_row, start_col, selected_text)
        
        # Show input field and save button
        mark_input = self.query_one("#mark-input", Input)
        mark_input.placeholder = f"Name for mark: '{selected_text[:20]}...'" if len(selected_text) > 20 else f"Name for mark: '{selected_text}'"
        mark_input.styles.display = "block"
        mark_input.focus()
        
        
        debug_log(f"Showing mark input for: '{selected_text}'")
    
    def save_pending_mark(self) -> None:
        """Save the pending mark with the name from the input field."""
        if not hasattr(self, '_pending_mark'):
            debug_log("No pending mark to save")
            return
        
        mark_input = self.query_one("#mark-input", Input)
        mark_name = mark_input.value.strip()
        
        if not mark_name:
            mark_name = "Unnamed Mark"
        
        # Get pending mark data
        page_num, start_row, start_col, selected_text = self._pending_mark
        
        # Create timestamp and save mark
        import time
        timestamp = time.time()
        mark_data = (page_num, start_row, start_col, selected_text, mark_name, timestamp)
        self.marks.append(mark_data)
        
        # Save marks to file
        self.save_marks()
        
        debug_log(f"Saved mark: '{mark_name}' ('{selected_text}') at page {page_num}")
        
        # Hide input field
        mark_input.value = ""
        mark_input.styles.display = "none"
        
        # Clear selection
        text_area = self.query_one("#text-area", TextArea)
        from textual.widgets.text_area import Selection
        text_area.selection = Selection(text_area.selection.end, text_area.selection.end)
        
        # Clear pending mark
        del self._pending_mark
    
    def cycle_color(self) -> None:
        """Cycle through colors and update the button appearance."""
        # Move to next color
        self.current_color_index = (self.current_color_index + 1) % len(self.highlight_colors)
        color_name, color_hex = self.highlight_colors[self.current_color_index]
        
        # Update the button text and color
        color_button = self.query_one("#color-button", Button)
        color_button.label = color_name
        color_button.styles.color = color_hex
        
        debug_log(f"Cycled to color: {color_name} ({color_hex})")
    
    def toggle_test_mark_dropdown(self) -> None:
        """Toggle the test mark dropdown to show/hide all highlights."""
        highlights_list = self.query_one("#highlights-list", ListView)
        test_mark_button = self.query_one("#test-mark-dropdown", Button)
        
        # Check current visibility state by looking at the button text
        current_label = str(test_mark_button.label)
        is_expanded = current_label.endswith("▲")
        
        if is_expanded:
            # Currently expanded, so collapse
            test_mark_button.label = "TEST MARK ▼"
            # Hide all highlights by clearing the list
            highlights_list.clear()
            debug_log("Collapsed test mark dropdown - cleared highlights")
        else:
            # Currently collapsed, so expand
            test_mark_button.label = "TEST MARK ▲"
            # Show all highlights by updating the list
            self.update_highlights_list()
            debug_log("Expanded test mark dropdown - showing all highlights")
    
    def save_focused_note(self) -> None:
        """Save the note from the last focused TextArea."""
        # Try current focus first, then fall back to last focused
        focused_widget = self.focused
        if (isinstance(focused_widget, TextArea) and 
            focused_widget.id and focused_widget.id.startswith("note_")):
            self.save_note_from_textarea(focused_widget)
        elif (self.last_focused_textarea and 
              isinstance(self.last_focused_textarea, TextArea) and 
              self.last_focused_textarea.id and self.last_focused_textarea.id.startswith("note_")):
            self.save_note_from_textarea(self.last_focused_textarea)
            debug_log(f"Saved note from last focused textarea: {self.last_focused_textarea.id}")
        else:
            debug_log("No note TextArea is focused or was last focused")
    
    def delete_focused_highlight(self) -> None:
        """Delete the highlight associated with the last focused TextArea."""
        # Try current focus first, then fall back to last focused
        focused_widget = self.focused
        target_widget = None
        
        if (isinstance(focused_widget, TextArea) and 
            focused_widget.id and focused_widget.id.startswith("note_")):
            target_widget = focused_widget
        elif (self.last_focused_textarea and 
              isinstance(self.last_focused_textarea, TextArea) and 
              self.last_focused_textarea.id and self.last_focused_textarea.id.startswith("note_")):
            target_widget = self.last_focused_textarea
            debug_log(f"Using last focused textarea for delete: {self.last_focused_textarea.id}")
        
        if target_widget:
            # Parse the ID to get coordinates: note_{page_num}_{start_row}_{start_col}
            parts = target_widget.id.split("_")
            if len(parts) >= 4:
                try:
                    page_num = int(parts[1])
                    start_row = int(parts[2])
                    start_col = int(parts[3])
                    
                    # Delete the highlight
                    self.update_highlight_note(page_num, start_row, start_col, "DELETE")
                    debug_log(f"Deleted highlight at page {page_num}")
                    
                except ValueError as e:
                    debug_log(f"Error parsing TextArea ID {target_widget.id}: {e}")
        else:
            debug_log("No note TextArea is focused or was last focused")
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection of a highlight in the ListView."""
        if event.list_view.id == "highlights-list" and hasattr(event.item, 'highlight_data'):
            page_num, full_text, start_row, start_col, note = event.item.highlight_data
            debug_log(f"Selected highlight on page {page_num + 1}")
            
            # Focus the textarea widget for this specific highlight
            try:
                input_id = f"note_{page_num}_{start_row}_{start_col}"
                note_input = self.query_one(f"#{input_id}", TextArea)
                note_input.focus()
                self.last_focused_textarea = note_input
            except Exception as e:
                debug_log(f"Could not focus textarea widget: {e}")
    
    def on_click(self, event) -> None:
        """Reset ListView background on click."""
        if (hasattr(event, 'widget') and 
            hasattr(event.widget, 'id') and 
            event.widget.id == "highlights-list"):
            try:
                event.widget.styles.background = "#1f1f39"
                event.widget.refresh()
            except Exception as e:
                debug_log(f"Could not reset background: {e}")
    
    def on_focus(self, event) -> None:
        """Track when TextAreas get focus for save/delete operations."""
        if (isinstance(event.widget, TextArea) and 
            hasattr(event.widget, 'id') and 
            event.widget.id and event.widget.id.startswith("note_")):
            self.last_focused_textarea = event.widget
            debug_log(f"Tracked focused textarea: {event.widget.id}")
    
    
    def update_highlight_color(self, page_num: int, start_row: int, start_col: int, new_color: str):
        """Update the color of a specific highlight."""
        if page_num in self.highlights:
            for i, highlight in enumerate(self.highlights[page_num]):
                start_pos, end_pos, text, note, color = parse_highlight_tuple(highlight)
                # Find the matching highlight by position
                if start_pos == (start_row, start_col):
                    # Strip existing brackets and rewrap with new color
                    clean_text = text.strip('[]{}()<>«»⟨⟩')
                    new_text = ColorManager.wrap_text_with_color(clean_text, new_color)
                    
                    # Update the highlight data
                    self.highlights[page_num][i] = (start_pos, end_pos, new_text, note, new_color)
                    debug_log(f"Updated highlight text to: {new_text}")
                    
                    # Refresh displays if needed
                    if page_num == self.current_page:
                        self.apply_simple_highlighting()
                    self.update_highlights_list()
                    break
    
    def on_key(self, event) -> None:
        """Handle key presses for note saving."""
        # Check if we have a focused TextArea that looks like a note input
        focused_widget = self.focused
        if (hasattr(event, 'key') and event.key == "ctrl+s" and 
            isinstance(focused_widget, TextArea) and 
            focused_widget.id and focused_widget.id.startswith("note_")):
            # Save note on Ctrl+S
            self.save_note_from_textarea(focused_widget)
        elif (hasattr(event, 'key') and event.key == "escape" and
              isinstance(focused_widget, TextArea) and 
              focused_widget.id and focused_widget.id.startswith("note_")):
            # Unfocus the TextArea on Escape
            focused_widget.blur()
    
    def save_note_from_textarea(self, textarea: TextArea) -> None:
        """Save note from a specific TextArea widget."""
        if not textarea.id or not textarea.id.startswith("note_"):
            return
            
        # Parse the ID to get coordinates: note_{page_num}_{start_row}_{start_col}
        parts = textarea.id.split("_")
        if len(parts) >= 4:
            try:
                page_num = int(parts[1])
                start_row = int(parts[2])
                start_col = int(parts[3])
                note_text = textarea.text.strip()
                
                # Update the highlight with the note
                self.update_highlight_note(page_num, start_row, start_col, note_text)
                debug_log(f"Saved note for highlight at page {page_num}: {note_text}")
                
                # Refresh the highlights list to show updated note
                self.update_highlights_list()
                
            except ValueError as e:
                debug_log(f"Error parsing TextArea ID {textarea.id}: {e}")
    
    def update_highlight_note(self, page_num: int, start_row: int, start_col: int, note_text: str) -> None:
        """Update the note for a specific highlight."""
        if note_text == "DELETE":
            # Remove the highlight entirely
            if page_num in self.highlights:
                self.highlights[page_num] = [
                    highlight 
                    for highlight in self.highlights[page_num]
                    if (highlight[0] if len(highlight) >= 1 else None) != (start_row, start_col)
                ]
                # Remove the page entry if no highlights remain
                if not self.highlights[page_num]:
                    del self.highlights[page_num]
                debug_log(f"Deleted highlight at page {page_num}")
                # Update page display to remove visual highlighting
                self.apply_simple_highlighting()
                # Update the highlights list in the right panel
                self.update_highlights_list()
        else:
            # Find and update the highlight with the note
            if page_num in self.highlights:
                for i, highlight in enumerate(self.highlights[page_num]):
                    start_pos, end_pos, text, old_note, color = parse_highlight_tuple(highlight)
                    if start_pos == (start_row, start_col):
                        # Update the highlight with the new note (preserve color info)
                        if len(highlight) == 4:
                            self.highlights[page_num][i] = (start_pos, end_pos, text, note_text, "yellow")
                        else:
                            self.highlights[page_num][i] = (start_pos, end_pos, text, note_text, color)
                        debug_log(f"Updated note for highlight: {note_text}")
                        break
        
        # Save highlights to file
        self.save_highlights()
    
    
    def _extract_selected_text(self, text_area: TextArea) -> str:
        """Extract and verify selected text from TextArea."""
        selected_text = text_area.selected_text
        selection = text_area.selection
        
        debug_log(f"Highlighting text: '{selected_text}'")
        debug_log(f"Selection start: {selection.start}, end: {selection.end}")
        
        # Manual text extraction to verify
        start_row, start_col = selection.start
        end_row, end_col = selection.end
        current_text = text_area.text
        lines = current_text.split('\n')
        
        if start_row < len(lines):
            if start_row == end_row:
                manual_text = lines[start_row][start_col:end_col + 1]
            else:
                # Multi-line selection - take from start to end of first line for now
                manual_text = lines[start_row][start_col:]
            debug_log(f"Manual extraction: '{manual_text}'")
            # Use manual extraction if it looks more complete
            if len(manual_text) > len(selected_text):
                selected_text = manual_text
                debug_log(f"Using manual extraction: '{selected_text}'")
        
        return selected_text
    
    def _create_highlight_data(self, selection, selected_text: str) -> tuple:
        """Create highlight data tuple with current color."""
        # Get current selected color and convert to full name
        color_name, _ = self.highlight_colors[self.current_color_index]
        full_color_name = ColorManager.get_full_color_name(color_name)
        
        # Wrap text with color brackets
        bracketed_text = ColorManager.wrap_text_with_color(selected_text, full_color_name)
        
        return (selection.start, selection.end, bracketed_text, "", full_color_name)
    
    def highlight_selected_text(self) -> None:
        """Highlight the currently selected text in the TextArea."""
        text_area = self.query_one("#text-area", TextArea)
        selection = text_area.selection
        
        if selection.start == selection.end:
            debug_log("No text selected for highlighting")
            return
        
        # Extract and verify selected text
        selected_text = self._extract_selected_text(text_area)
        
        # Store the highlight for this page
        page_num = self.current_page
        if page_num not in self.highlights:
            self.highlights[page_num] = []
        
        # Create and store highlight data
        highlight_data = self._create_highlight_data(selection, selected_text)
        self.highlights[page_num].append(highlight_data)
        debug_log(f"Stored highlight for page {page_num}: {highlight_data}")
        
        # Update displays and save
        self.apply_simple_highlighting()
        self.update_highlights_list()
        self.save_highlights()
    
    def apply_simple_highlighting(self) -> None:
        """Apply custom tree-sitter highlighting using brackets around highlighted text."""
        text_area = self.query_one("#text-area", TextArea)
        page_num = self.current_page
        original_text = self.pages[page_num]
        
        # If no highlights on this page, just show original text
        if page_num not in self.highlights or not self.highlights[page_num]:
            text_area.text = original_text
            return
        
        # Apply bracket highlighting for custom tree-sitter highlighting
        highlighted_text = original_text
        # Sort highlights by position (reverse order to avoid position shifts)
        sorted_highlights = sorted(self.highlights[page_num], key=lambda h: h[0], reverse=True)
        
        for highlight in sorted_highlights:
            _, _, selected_text, note, color = parse_highlight_tuple(highlight)
            # The text already has proper color brackets, use as-is
            highlighted_version = selected_text
            
            # Extract the text without brackets for replacement
            clean_text = selected_text.strip('[]{}()<>«»⟨⟩')
            highlighted_text = highlighted_text.replace(clean_text, highlighted_version)
        
        text_area.text = highlighted_text
        debug_log(f"Applied bracket highlighting to page {page_num}")
    
    def _collect_all_highlights(self) -> list:
        """Collect and sort all highlights from all pages."""
        all_highlights = []
        for page_num, page_highlights in self.highlights.items():
            for highlight in page_highlights:
                start_pos, end_pos, text, note, color = parse_highlight_tuple(highlight)
                start_row, start_col = start_pos
                all_highlights.append((page_num, text, text, start_row, start_col, note, color))
        
        # Sort highlights by page number, then by position in text
        all_highlights.sort(key=lambda x: (x[0], x[3], x[4]))  # page, start_row, start_col
        return all_highlights
    
    def _create_highlight_list_item(self, page_num: int, full_text: str, start_row: int, 
                                   start_col: int, note: str, color: str) -> ListItem:
        """Create a ListView item for a highlight."""
        # Get hex color for display
        hex_color = ColorManager.get_hex(color)
        
        # Strip bracket characters from the text for clean display
        clean_text = ColorManager.strip_brackets(full_text, color)
        
        # Create styled display with white page number and proper color highlight
        page_part = f"[white]Page {page_num + 1}:[/white]"
        highlight_part = f"[{hex_color}]{clean_text}[/{hex_color}]"
        display_text = f"{page_part} {highlight_part}"
        
        # Create vertical layout with display text and editable textarea for note
        note_area = TextArea(
            text=note if note else "",
            id=f"note_{page_num}_{start_row}_{start_col}",
            read_only=False
        )
        note_area.show_line_numbers = False
        
        content = Vertical(Label(display_text), note_area)
        highlight_item = ListItem(content)
        
        # Store full data as metadata for note editing
        highlight_item.highlight_data = (page_num, full_text, start_row, start_col, note)
        return highlight_item
    
    def update_highlights_list(self) -> None:
        """Update the highlights ListView with all highlights and marks from all pages."""
        highlights_list = self.query_one("#highlights-list", ListView)
        highlights_list.clear()
        
        # Collect all highlights and marks, then sort by position
        all_items = []
        
        # Add highlights
        all_highlights = self._collect_all_highlights()
        for page_num, _, full_text, start_row, start_col, note, color in all_highlights:
            all_items.append(('highlight', page_num, start_row, start_col, full_text, note, color))
        
        # Add marks (handle both old and new mark formats)
        for mark in self.marks:
            if len(mark) == 6:
                # New format: (page_num, start_row, start_col, selected_text, mark_name, timestamp)
                page_num, start_row, start_col, selected_text, mark_name, timestamp = mark
            else:
                # Old format or incomplete mark - use defaults
                if len(mark) == 5:
                    page_num, start_row, start_col, selected_text, mark_name = mark
                else:
                    debug_log(f"Unexpected mark format with {len(mark)} values: {mark}")
                    continue
                timestamp = 0
            all_items.append(('mark', page_num, start_row, start_col, selected_text, mark_name, None))
        
        # Sort by position (page, row, col)
        all_items.sort(key=lambda x: (x[1], x[2], x[3]))
        
        # Create list items
        for item in all_items:
            if item[0] == 'highlight':
                _, page_num, start_row, start_col, full_text, note, color = item
                highlight_item = self._create_highlight_list_item(
                    page_num, full_text, start_row, start_col, note, color
                )
                highlights_list.append(highlight_item)
            elif item[0] == 'mark':
                _, page_num, start_row, start_col, selected_text, mark_name, _ = item
                mark_item = self._create_mark_list_item(page_num, mark_name, selected_text)
                highlights_list.append(mark_item)
        
        debug_log(f"Updated highlights list with {len(all_highlights)} highlights and {len(self.marks)} marks")
    
    
    
    def _create_mark_list_item(self, page_num: int, mark_name: str, selected_text: str) -> ListItem:
        """Create a ListItem for a mark."""
        # Create mark button similar to TEST MARK
        mark_button = Button(f"{mark_name.upper()} ▼", id=f"mark-{mark_name.lower().replace(' ', '-')}")
        mark_button.can_focus = False
        mark_button.active_effect_duration = 0
        mark_button.styles.color = "#ffffff"
        mark_button.styles.width = "100%"
        mark_button.styles.text_align = "left"
        mark_button.styles.margin = (1, 0, 0, 0)
        
        # Create and return the ListItem with the button as content
        item = ListItem(mark_button)
        return item
    
    def watch_current_page(self) -> None:
        counter_widget = self.query_one("#counter", Static)
        progress_widget = self.query_one("#progress", ProgressBar)
        
        # Log to file
        debug_log(f"Page {self.current_page + 1}: navigating...")
        
        # Update TextArea display with highlights
        self.apply_simple_highlighting()
        
        counter_widget.update(f"{self.current_page + 1} / {len(self.pages)}")
        progress_widget.update(progress=self.current_page + 1)
        
        debug_log(f"Progress updated to: {self.current_page + 1}/{len(self.pages)}")
    
    def save_highlights(self) -> None:
        """Save highlights to a pickle file."""
        try:
            with open('highlights.pkl', 'wb') as f:
                pickle.dump(self.highlights, f)
            debug_log(f"Saved {len(self.highlights)} pages of highlights")
        except Exception as e:
            debug_log(f"Error saving highlights: {e}")
    
    def load_highlights(self) -> None:
        """Load highlights from a pickle file."""
        try:
            if os.path.exists('highlights.pkl'):
                with open('highlights.pkl', 'rb') as f:
                    self.highlights = pickle.load(f)
                debug_log(f"Loaded {len(self.highlights)} pages of highlights")
                
                # Convert old format highlights to new format with default yellow color
                for page_num, page_highlights in self.highlights.items():
                    updated_highlights = []
                    for highlight in page_highlights:
                        if len(highlight) == 4:
                            # Old format: (start_pos, end_pos, text, note)
                            start_pos, end_pos, text, note = highlight
                            # Add yellow as default color, ensure text has yellow brackets
                            if not (text.startswith('[') and text.endswith(']')):
                                # Add yellow brackets if they're missing
                                clean_text = text.strip('[]{}()<>«»⟨⟩')
                                text = f"[{clean_text}]"
                            updated_highlights.append((start_pos, end_pos, text, note, "yellow"))
                        else:
                            # New format: keep as-is
                            updated_highlights.append(highlight)
                    self.highlights[page_num] = updated_highlights
                    
                debug_log("Converted old highlight format to new format with colors")
            else:
                debug_log("No highlights file found, starting fresh")
        except Exception as e:
            debug_log(f"Error loading highlights: {e}")
            
        # Load marks
        self.load_marks()
    
    def save_marks(self) -> None:
        """Save marks to a pickle file."""
        try:
            with open('marks.pkl', 'wb') as f:
                pickle.dump(self.marks, f)
            debug_log(f"Saved {len(self.marks)} marks")
        except Exception as e:
            debug_log(f"Error saving marks: {e}")
    
    def load_marks(self) -> None:
        """Load marks from a pickle file."""
        try:
            with open('marks.pkl', 'rb') as f:
                self.marks = pickle.load(f)
            debug_log(f"Loaded {len(self.marks)} marks")
        except FileNotFoundError:
            debug_log("No marks file found, starting fresh")
            self.marks = []
        except Exception as e:
            debug_log(f"Error loading marks: {e}")
            self.marks = []
    
    def on_mount(self) -> None:
        """Called when the app is mounted and ready."""
        # Now that the UI is ready, update displays with loaded highlights
        if self.highlights:
            # Don't show highlights initially - let the dropdown control visibility
            self.apply_simple_highlighting()
        
        # Update the highlights list to show marks and highlights
        self.update_highlights_list()
        
        # Force override the ListView background after mounting
        try:
            highlights_list = self.query_one("#highlights-list", ListView)
            highlights_list.styles.background = "#1f1f39"
            highlights_list.refresh()
            debug_log("Forced ListView background override after mounting")
        except Exception as e:
            debug_log(f"Could not override ListView background: {e}")
        
        


if __name__ == "__main__":
    app = EPUBReader()
    app.run()
