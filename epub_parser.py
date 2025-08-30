#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zipfile
import re
import sys
import pickle
import os
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static, TextArea, ProgressBar, ListView, ListItem, Label, Input
from textual.reactive import reactive
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
    
    #paragraph {
        margin: 1 1 0 1;
        padding: 1;
        border: solid #9aa4ca;
        background: #1f1f39;
        color: #ffffff;
        text-align: left;
        height: 0.5fr;
    }
    
    TextArea {
        background: #1f1f39;
        color: #ffffff;
    }
    
    #left-controls {
        height: auto;
        min-height: 3;
        background: #1f1f39;
        border: solid #9aa4ca;
        margin: 0 1 1 1;
        padding: 1;
        min-width: 0;
        overflow: auto;
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
        color: #ffffff;
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
    
    #counter {
        text-align: center;
        width: 1fr;
        color: #9aa4ca;
        background: #1f1f39;
    }
    
    #progress {
        width: 2fr;
        margin: 0 1;
    }
    
    ProgressBar {
        background: #1f1f39;
        color: #9aa4ca;
    }
    """
    
    current_page = reactive(0)
    
    def __init__(self):
        super().__init__()
        self.pages = all_pages
        # Store highlights as {page_number: [(start_pos, end_pos, text, note), ...]}
        self.highlights = {}
        self.selected_highlight = None  # Track currently selected highlight for note editing
        # Load existing highlights
        self.load_highlights()
    
    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="main-content"):
                with Vertical(id="left-panel"):
                    yield TextArea(self.pages[0] if self.pages else "No content", id="paragraph", read_only=True)
                    with Horizontal(id="left-controls"):
                        yield Button("Prev", id="prev")
                        yield ProgressBar(total=len(self.pages), show_percentage=False, show_eta=False, id="progress")
                        yield Static(f"1 / {len(self.pages)}", id="counter")
                        yield Button("Next", id="next")
                        yield Button("Highlight", id="highlight")
                with Vertical(id="notes-panel"):
                    yield Static("HIGHLIGHTS & NOTES", id="notes-title")
                    yield ListView(id="highlights-list")
                    yield TextArea("Click a highlight to add a note...", id="note-input", read_only=True)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "next" and self.current_page < len(self.pages) - 1:
            self.current_page += 1
        elif event.button.id == "prev" and self.current_page > 0:
            self.current_page -= 1
        elif event.button.id == "highlight":
            self.highlight_selected_text()
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection of a highlight in the ListView."""
        if event.list_view.id == "highlights-list" and hasattr(event.item, 'highlight_data'):
            debug_log(f"Raw highlight_data: {event.item.highlight_data}")
            page_num, full_text, start_row, start_col, note = event.item.highlight_data
            debug_log(f"Selected highlight on page {page_num + 1}: {full_text[:50]}...")
            debug_log(f"Note value from data: '{note}' (type: {type(note)})")
            
            # Store selected highlight for note editing
            self.selected_highlight = (page_num, start_row, start_col)
            
            # Show and focus the note input
            note_input = self.query_one("#note-input", TextArea)
            note_input.styles.visibility = "visible"
            note_input.read_only = False
            # Set existing note or empty text
            if note and note != "TEST FROM SELECTION - Type your note here":
                note_input.text = note
            else:
                note_input.text = ""
            note_input.focus()
            debug_log(f"TextArea text set to: '{note_input.text}'")
    
    def on_key(self, event) -> None:
        """Handle key presses for note saving."""
        note_input = self.query_one("#note-input", TextArea)
        if hasattr(event, 'key') and event.key == "enter" and note_input.styles.visibility == "visible":
            # Save note on Enter
            self.save_current_note()
            note_input.styles.visibility = "hidden"
            note_input.read_only = True
            note_input.text = "Click a highlight to add a note..."
            self.selected_highlight = None
        elif hasattr(event, 'key') and event.key == "escape":
            # Hide note input on Escape without saving
            if note_input.styles.visibility == "visible":
                note_input.styles.visibility = "hidden"
                note_input.read_only = True
                note_input.text = "Click a highlight to add a note..."
                self.selected_highlight = None
    
    def save_current_note(self) -> None:
        """Save the current note being edited."""
        if self.selected_highlight:
            note_input = self.query_one("#note-input", TextArea)
            note_text = note_input.text.strip()
            page_num, start_row, start_col = self.selected_highlight
            
            # Check if user wants to delete the highlight
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
            
            # Update the display
            self.update_highlights_list()
            # Save highlights to file
            self.save_highlights()
    
    def highlight_selected_text(self) -> None:
        """Highlight the currently selected text in the TextArea."""
        text_area = self.query_one("#paragraph", TextArea)
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
        """Apply simple text-based highlighting using colored background markers."""
        text_area = self.query_one("#paragraph", TextArea)
        page_num = self.current_page
        original_text = self.pages[page_num]
        
        # If no highlights on this page, just show original text
        if page_num not in self.highlights or not self.highlights[page_num]:
            text_area.text = original_text
            return
        
        # Apply highlighting by surrounding text with colored Unicode block characters
        highlighted_text = original_text
        for _, _, selected_text, _ in reversed(self.highlights[page_num]):
            # Replace the selected text with highlighted version using Unicode blocks
            highlighted_text = highlighted_text.replace(
                selected_text, 
                f"█▌{selected_text}▐█"
            )
        
        text_area.text = highlighted_text
        debug_log(f"Applied block highlighting to page {page_num}")
    
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
            # Create full display text with highlight and note
            full_display = f"Page {page_num + 1}:\n\n{full_text}"
            if note:
                full_display += f"\n\n{note}"
            
            highlight_item = ListItem(
                Label(full_display)
            )
            # Store full data as metadata for note editing
            highlight_item.highlight_data = (page_num, full_text, start_row, start_col, note)
            highlights_list.append(highlight_item)
        
        debug_log(f"Updated highlights list with {len(all_highlights)} highlights")
    
    def update_page_with_highlights(self) -> None:
        """Update the current page display with highlights."""
        self.apply_simple_highlighting()
    
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
        paragraph_widget = self.query_one("#paragraph", TextArea)
        counter_widget = self.query_one("#counter", Static)
        progress_widget = self.query_one("#progress", ProgressBar)
        
        # Log to file
        debug_log(f"Page {self.current_page + 1}: navigating...")
        debug_log(f"Widget found: {paragraph_widget}")
        
        # Update the page with highlights if any exist
        self.update_page_with_highlights()
        
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


if __name__ == "__main__":
    app = EPUBReader()
    app.run()
