#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zipfile
import re
import sys
import pickle
import os
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static, TextArea, ProgressBar, ListView, ListItem, Label, Input, Select
from textual.widgets.text_area import TextAreaTheme
from rich.style import Style
from textual.reactive import reactive
from tree_sitter_parser import tree_sitter_language
# Debug logging function
def debug_log(message):
    with open('log.txt', 'a') as f:
        f.write(f"{message}\n")
        f.flush()

# Load paragraphs from EPUB
debug_log("Starting EPUB loading...")
epub_file = zipfile.ZipFile('bookshelf/gravitys-rainbow.epub', 'r')
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

epub_file.close()
debug_log(f"Loaded {len(all_paragraphs)} paragraphs total")

# Group paragraphs into exactly 776 pages
def create_pages(paragraphs, total_pages=776):
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

all_pages = create_pages(all_paragraphs)
debug_log(f"Created {len(all_pages)} pages from paragraphs")


class EPUBReader(App):
    CSS = """
    Screen {
        background: #1f1f39;
    }
    
    #main-content {
        height: 100vh;
    }
    
    #left-panel {
        width: 50%;
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
        width: 50%;
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
        color: #fbdda7 !important;
    }
    
    Static#counter {
        color: #fbdda7 !important;
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
    
    #highlight-controls {
        height: auto;
        border: solid #9aa4ca;
        margin: 1;
        padding: 1;
        align: center middle;
    }
    
    #counter {
        text-align: center;
        width: 1fr;
        color: #9aa4ca;
        background: #1f1f39;
    }
    
    #notes-title {
        color: #6be28d;
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
        max-height: 8;
        border: none;
        margin: 0;
        padding: 1;
        background: #1f1f39;
        color: #9aa4ca;
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
    """
    
    current_page = reactive(0)
    
    def __init__(self):
        super().__init__()
        self.pages = all_pages
        # Store highlights as {page_number: [(start_pos, end_pos, text, note), ...]}
        self.highlights = {}
        self.selected_highlight = None  # Track currently selected highlight for note editing
        self.last_focused_textarea = None  # Track the last focused TextArea for save/delete operations
        # Load existing highlights
        self.load_highlights()
    
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
                        with Horizontal():
                            yield Button("Back", id="prev")
                            yield ProgressBar(total=len(self.pages), show_percentage=False, show_eta=False, id="progress")
                            yield Button("Next", id="next")
                        yield Static(f"1 / {len(self.pages)}", id="counter")
                    with Horizontal(id="highlight-controls"):
                        yield Button("Highlight", id="highlight")
                        yield Button("Save", id="save-note")
                        yield Button("Delete", id="delete-highlight")
                with Vertical(id="notes-panel"):
                    yield Static("HIGHLIGHTS & NOTES", id="notes-title")
                    highlights_list = ListView(id="highlights-list")
                    highlights_list.styles.background = "#1f1f39"
                    # Disable ListView's built-in selection behavior
                    highlights_list.can_focus = False
                    yield highlights_list
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "next" and self.current_page < len(self.pages) - 1:
            self.current_page += 1
        elif event.button.id == "prev" and self.current_page > 0:
            self.current_page -= 1
        elif event.button.id == "highlight":
            self.highlight_selected_text()
        elif event.button.id == "save-note":
            self.save_focused_note()
        elif event.button.id == "delete-highlight":
            self.delete_focused_highlight()
    
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
        debug_log(f"ListView selected event triggered - ListView ID: {event.list_view.id}")
        debug_log(f"Selected item type: {type(event.item)}")
        debug_log(f"Selected item has highlight_data: {hasattr(event.item, 'highlight_data')}")
        debug_log(f"Event widget: {getattr(event, 'widget', 'N/A')}")
        debug_log(f"Event attributes: {dir(event)}")
        
        if event.list_view.id == "highlights-list" and hasattr(event.item, 'highlight_data'):
            debug_log(f"Raw highlight_data: {event.item.highlight_data}")
            page_num, full_text, start_row, start_col, note = event.item.highlight_data
            debug_log(f"Selected highlight on page {page_num + 1}: {full_text[:50]}...")
            debug_log(f"Note value from data: '{note}' (type: {type(note)})")
            
            # Store selected highlight for note editing
            self.selected_highlight = (page_num, start_row, start_col)
            
            # Focus the textarea widget for this specific highlight
            try:
                input_id = f"note_{page_num}_{start_row}_{start_col}"
                note_input = self.query_one(f"#{input_id}", TextArea)
                note_input.focus()
                self.last_focused_textarea = note_input  # Track this as the last focused
                debug_log(f"Focused textarea widget: {input_id}")
            except Exception as e:
                debug_log(f"Could not focus textarea widget: {e}")
        else:
            debug_log("ListView selection event but not on highlights-list or no highlight_data")
    
    def on_click(self, event) -> None:
        """Log all click events to debug highlighting issues."""
        debug_log(f"Click event - Widget: {event.widget}, Type: {type(event.widget)}")
        debug_log(f"Click coordinates: x={event.x}, y={event.y}")
        debug_log(f"Widget ID: {getattr(event.widget, 'id', 'No ID')}")
        debug_log(f"Widget classes: {getattr(event.widget, 'classes', 'No classes')}")
        debug_log(f"Event style: {getattr(event, 'style', 'No style')}")
        
        # If clicking on the ListView container itself (not an item), try to prevent highlighting
        if (hasattr(event, 'widget') and 
            hasattr(event.widget, 'id') and 
            event.widget.id == "highlights-list"):
            try:
                # Force background reset immediately after click
                event.widget.styles.background = "#1f1f39"
                event.widget.refresh()
                debug_log("Reset ListView background after click")
            except Exception as e:
                debug_log(f"Could not reset background: {e}")
    
    def on_focus(self, event) -> None:
        """Track when TextAreas get focus for save/delete operations."""
        if (isinstance(event.widget, TextArea) and 
            hasattr(event.widget, 'id') and 
            event.widget.id and event.widget.id.startswith("note_")):
            self.last_focused_textarea = event.widget
            debug_log(f"Tracked focused textarea: {event.widget.id}")
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle color selection change for highlights."""
        if event.select.id and event.select.id.startswith("color_select_"):
            # Parse the select ID to get highlight coordinates
            parts = event.select.id.split("_")
            if len(parts) >= 5:  # color_select_{page_num}_{start_row}_{start_col}
                page_num = int(parts[2])
                start_row = int(parts[3])
                start_col = int(parts[4])
                new_color = event.value
                
                debug_log(f"Color changed for highlight at page {page_num}, row {start_row}, col {start_col} to {new_color}")
                
                # Update the highlight in memory and refresh display
                self.update_highlight_color(page_num, start_row, start_col, new_color)
    
    def update_highlight_color(self, page_num: int, start_row: int, start_col: int, new_color: str):
        """Update the color of a specific highlight."""
        if page_num in self.highlights:
            for i, (start_pos, end_pos, text, note) in enumerate(self.highlights[page_num]):
                # Find the matching highlight by position
                if start_pos == (start_row, start_col):
                    # Update the highlight text with new color brackets
                    color_brackets = {
                        "yellow": ("[", "]"),
                        "green": ("{", "}"),
                        "red": ("<", ">"),
                        "blue": ("«", "»"),
                        "white": ("⟨", "⟩")
                    }
                    
                    if new_color in color_brackets:
                        open_bracket, close_bracket = color_brackets[new_color]
                        new_text = f"{open_bracket}{text.strip('[]{}()<>«»⟨⟩')}{close_bracket}"
                        
                        # Update the highlight data
                        self.highlights[page_num][i] = (start_pos, end_pos, new_text, note)
                        debug_log(f"Updated highlight text to: {new_text}")
                        
                        # Refresh the page display if it's the current page
                        if page_num == self.current_page:
                            self.update_page()
                        
                        # Refresh the highlights list
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
                    (start_pos, end_pos, text, old_note) 
                    for start_pos, end_pos, text, old_note in self.highlights[page_num]
                    if start_pos != (start_row, start_col)
                ]
                # Remove the page entry if no highlights remain
                if not self.highlights[page_num]:
                    del self.highlights[page_num]
                debug_log(f"Deleted highlight at page {page_num}")
                # Update page display to remove visual highlighting
                self.apply_simple_highlighting()
        else:
            # Find and update the highlight with the note
            if page_num in self.highlights:
                for i, (start_pos, end_pos, text, old_note) in enumerate(self.highlights[page_num]):
                    if start_pos == (start_row, start_col):
                        # Update the highlight with the new note
                        self.highlights[page_num][i] = (start_pos, end_pos, text, note_text)
                        debug_log(f"Updated note for highlight: {note_text}")
                        break
        
        # Save highlights to file
        self.save_highlights()
    
    
    def highlight_selected_text(self) -> None:
        """Highlight the currently selected text in the TextArea."""
        text_area = self.query_one("#text-area", TextArea)
        selection = text_area.selection
        
        if selection.start == selection.end:
            # No text selected
            debug_log("No text selected for highlighting")
            return
            
        # Get the selected text
        selected_text = text_area.selected_text
        debug_log(f"Highlighting text: '{selected_text}'")
        debug_log(f"Selection start: {selection.start}, end: {selection.end}")
        debug_log(f"Selected text length: {len(selected_text)}")
        
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
        
        # Store the highlight for this page
        page_num = self.current_page
        if page_num not in self.highlights:
            self.highlights[page_num] = []
        
        # Add this highlight to the page's highlights (with empty note initially)
        highlight_data = (selection.start, selection.end, selected_text, "")
        self.highlights[page_num].append(highlight_data)
        debug_log(f"Stored highlight for page {page_num}: {highlight_data}")
        
        # Apply simple text replacement highlighting (no Rich markup)
        self.apply_simple_highlighting()
        
        # Update highlights list in notes panel
        self.update_highlights_list()
        # Save highlights to file
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
        
        for _, _, selected_text, note in sorted_highlights:
            # Determine bracket type based on note or default to yellow
            if note and note.startswith("GREEN:"):
                highlighted_version = f'{{{selected_text}}}'  # Green curly braces
            elif note and note.startswith("RED:"):
                highlighted_version = f'<{selected_text}>'    # Red angle brackets
            elif note and note.startswith("BLUE:"):
                highlighted_version = f'«{selected_text}»'    # Blue guillemets
            else:
                highlighted_version = f'[{selected_text}]'    # Default yellow square brackets
            
            highlighted_text = highlighted_text.replace(selected_text, highlighted_version)
        
        text_area.text = highlighted_text
        debug_log(f"Applied bracket highlighting to page {page_num}")
    
    def update_highlights_list(self) -> None:
        """Update the highlights ListView with all highlights from all pages."""
        highlights_list = self.query_one("#highlights-list", ListView)
        highlights_list.clear()
        
        # Collect all highlights from all pages
        all_highlights = []
        for page_num, page_highlights in self.highlights.items():
            for start_pos, end_pos, text, note in page_highlights:
                start_row, start_col = start_pos
                all_highlights.append((page_num, text, text, start_row, start_col, note))
        
        # Sort highlights by page number, then by position in text
        all_highlights.sort(key=lambda x: (x[0], x[3], x[4]))  # page, start_row, start_col
        
        # Add highlights to ListView
        for page_num, display_text, full_text, start_row, start_col, note in all_highlights:
            # Create styled display with white page number and yellow highlight
            page_part = f"[white]Page {page_num + 1}:[/white]"
            highlight_part = f"[#fbdda7]{full_text}[/#fbdda7]"
            display_text = f"{page_part} {highlight_part}"
            
            # Create vertical layout with display text and editable textarea for note only
            note_area = TextArea(
                text=note if note else "",
                id=f"note_{page_num}_{start_row}_{start_col}",
                read_only=False
            )
            note_area.show_line_numbers = False
            
            content = Vertical(
                Label(display_text),
                note_area
            )
            
            highlight_item = ListItem(content)
            # Store full data as metadata for note editing
            highlight_item.highlight_data = (page_num, full_text, start_row, start_col, note)
            highlights_list.append(highlight_item)
        
        debug_log(f"Updated highlights list with {len(all_highlights)} highlights")
    
    
    def apply_highlight_markup(self, text: str, highlights: list) -> str:
        """Apply Rich markup to highlight text segments."""
        # Sort highlights by start position (reverse order to avoid position shifts)
        sorted_highlights = sorted(highlights, key=lambda h: h[0], reverse=True)
        
        # Convert text to list of lines for easier manipulation
        lines = text.split('\n')
        
        for start_pos, end_pos, _ in sorted_highlights:
            start_row, start_col = start_pos
            end_row, end_col = end_pos
            
            if start_row < len(lines) and end_row < len(lines):
                if start_row == end_row:
                    # Single line highlight
                    line = lines[start_row]
                    highlighted_line = (
                        line[:start_col] + 
                        f"[bold yellow on blue]{line[start_col:end_col]}[/bold yellow on blue]" +
                        line[end_col:]
                    )
                    lines[start_row] = highlighted_line
                else:
                    # Multi-line highlight (for future enhancement)
                    # For now, just highlight the first line
                    line = lines[start_row]
                    highlighted_line = (
                        line[:start_col] + 
                        f"[bold yellow on blue]{line[start_col:]}[/bold yellow on blue]"
                    )
                    lines[start_row] = highlighted_line
        
        return '\n'.join(lines)
    
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
            else:
                debug_log("No highlights file found, starting fresh")
        except Exception as e:
            debug_log(f"Error loading highlights: {e}")
            self.highlights = {}
    
    def on_mount(self) -> None:
        """Called when the app is mounted and ready."""
        # Now that the UI is ready, update displays with loaded highlights
        if self.highlights:
            self.update_highlights_list()
            self.apply_simple_highlighting()
        
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
