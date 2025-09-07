#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zipfile
import re
import pickle
import os
import urllib.request
import urllib.parse
import requests
import argparse
import time
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Center, Middle
from textual.screen import Screen
from textual.widgets import Button, Static, TextArea, ProgressBar, ListView, ListItem, Label, OptionList, Input
from textual.screen import ModalScreen

# Try to import textual-image for image display
try:
    from textual_image.widget import Image as TextualImage
    TEXTUAL_IMAGE_AVAILABLE = True
except ImportError:
    TEXTUAL_IMAGE_AVAILABLE = False

try:
    from textual_imageview import ImageViewer
    IMAGEVIEW_AVAILABLE = True
except ImportError:
    IMAGEVIEW_AVAILABLE = False
from textual.widgets.text_area import TextAreaTheme
from rich.style import Style
from textual.reactive import reactive
from textual.events import Click
import webbrowser
from syntax.manager import tree_sitter_language

# Try to import textual-serve for server mode
try:
    from textual_serve.server import Server
    TEXTUAL_SERVE_AVAILABLE = True
except ImportError:
    TEXTUAL_SERVE_AVAILABLE = False
# Debug logging function
def debug_log(message):
    with open('log.txt', 'a') as f:
        f.write(f"{message}\n")
        f.flush()

# Custom clickable image widget
class ClickableImage(Vertical):
    """A clickable image widget that opens URL when clicked."""
    
    def __init__(self, image_path: str, image_url: str, **kwargs):
        super().__init__(**kwargs)
        self.image_url = image_url
        self.image_path = image_path
        
        # Create the actual image widget
        if TEXTUAL_IMAGE_AVAILABLE:
            self.image_widget = TextualImage(image_path)
        elif IMAGEVIEW_AVAILABLE:
            self.image_widget = ImageViewer(image_path)
        else:
            self.image_widget = Static(f"Image: {os.path.basename(image_path)}")
            
        self.image_widget.add_class("note-image")
    
    def compose(self) -> ComposeResult:
        yield self.image_widget
    
    def on_click(self, event: Click) -> None:
        """Open the image URL in browser when clicked."""
        debug_log(f"Image clicked, opening URL: {self.image_url}")
        try:
            webbrowser.open(self.image_url)
        except Exception as e:
            debug_log(f"Error opening URL: {e}")
    

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
        "white": ("|", "|")
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
        width: 50%;
        margin: 1;
        padding: 1;
        border: solid #9aa4ca;
        background: #1f1f39;
        color: #ffffff;
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
    
    /* Mark items without borders */
    ListItem.mark-item {
        border: none;
        padding: 0;
        margin: 0;
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
    
    /* Image widget styling for ListView items */
    .note-image {
        height: auto;
        max-height: 25;
        width: 100%;
        margin: 1 0;
        align: center middle;
    }
    
    /* Clickable image container styling */
    ClickableImage {
        border: solid transparent;
    }
    
    ClickableImage:hover {
        border: solid #9aa4ca;
        background: #2a2a5a;
    }
    
    /* Remove borders from ListItems containing images */
    ListView ListItem.image-container {
        border: none;
        padding: 0;
        margin: 0;
        background: #1f1f39;
    }
    
    """
    
    current_page = reactive(0)
    
    def __init__(self):
        super().__init__()
        self.pages = self._load_epub_content()
        # Store highlights as {page_number: [(start_pos, end_pos, text, note, color), ...]}
        self.highlights = {}
        self.last_focused_textarea = None  # Track the last focused TextArea for save/delete operations
        self.last_clicked_mark = None  # Track the last clicked mark for delete operations
        self.last_interaction_type = None  # 'note' or 'mark' to track which was interacted with last
        self.mark_dropdown_states = {}  # Track which marks are expanded (True) or collapsed (False)
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
    
    def download_image(self, url: str) -> str:
        """Download image from URL to images directory and return filepath."""
        try:
            # Create images directory if it doesn't exist
            images_dir = Path("images")
            images_dir.mkdir(exist_ok=True)
            
            # Get filename from URL
            parsed_url = urllib.parse.urlparse(url)
            filename = os.path.basename(parsed_url.path)
            
            # If no filename, generate one
            if not filename or '.' not in filename:
                filename = f"image_{hash(url) % 10000}.jpg"
            
            filepath = images_dir / filename
            
            # Check if already downloaded
            if filepath.exists():
                return str(filepath)
            
            # Download the image with proper headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Save to file
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return str(filepath)
            
        except Exception as e:
            debug_log(f"Image download failed: {e}")
            return None
    
    def process_note_for_images(self, note_text: str) -> tuple:
        """Process note text to find and download image URLs, return (processed_text, image_data)."""
        # Pattern to find URLs ending in .jpg or .png
        image_pattern = r'https?://[^\s]+\.(?:jpg|png)(?:\?[^\s]*)?'
        
        image_urls = re.findall(image_pattern, note_text, re.IGNORECASE)
        image_data = []  # List of (url, filepath) tuples
        processed_text = note_text
        
        # Check if we're running in server mode (via command line args)
        import sys
        is_server_mode = '--server' in sys.argv
        
        for url in image_urls:
            filepath = self.download_image(url)
            if filepath:
                image_data.append((url, filepath))
                
                if is_server_mode:
                    # In server mode, convert URL to a hyperlink using rich markup
                    hyperlink = f"[link={url}]{url}[/link]"
                    processed_text = processed_text.replace(url, hyperlink)
                else:
                    # In local mode, hide the URL (original behavior)
                    processed_text = processed_text.replace(url, "")
        
        # Clean up extra whitespace only if URLs were removed (local mode)
        if not is_server_mode:
            processed_text = re.sub(r'\s+', ' ', processed_text).strip()
        
        return processed_text, image_data
    
    def _process_note_images(self, note_text: str) -> list:
        """Process note text for images and return list of image widgets."""
        image_widgets = []
        
        if not note_text:
            debug_log("No note text provided for image processing")
            return image_widgets
            
        processed_text, image_data = self.process_note_for_images(note_text)
        debug_log(f"Found {len(image_data)} image data: {image_data}")
        
        # Create image widgets for each downloaded image
        for url, image_path in image_data:
            try:
                if TEXTUAL_IMAGE_AVAILABLE:
                    debug_log(f"Creating TextualImage widget for {image_path}")
                    image_widget = TextualImage(image_path)
                    image_widgets.append(image_widget)
                    debug_log(f"Successfully created TextualImage widget")
                elif IMAGEVIEW_AVAILABLE:
                    debug_log(f"Creating ImageViewer widget for {image_path}")
                    image_widget = ImageViewer(image_path) 
                    image_widgets.append(image_widget)
                    debug_log(f"Successfully created ImageViewer widget")
                else:
                    debug_log("No image display libraries available")
            except Exception as e:
                debug_log(f"Failed to create image widget for {image_path}: {e}")
        
        debug_log(f"Returning {len(image_widgets)} image widgets")
        return image_widgets
    
    def _reconstruct_note_with_urls(self, page_num: int, start_row: int, start_col: int, processed_text: str) -> str:
        """Reconstruct the original note with URLs from the existing highlight data."""
        # Find the existing highlight to get the original note text
        if page_num in self.highlights:
            for highlight in self.highlights[page_num]:
                start_pos, end_pos, text, original_note, color = parse_highlight_tuple(highlight)
                if start_pos == (start_row, start_col):
                    # Check if original note has URLs that were processed out
                    if original_note:
                        _, original_image_data = self.process_note_for_images(original_note)
                        if original_image_data:
                            # The processed text might be missing URLs, keep the original URLs
                            # But allow other text to be updated
                            image_pattern = r'https?://[^\s]+\.(?:jpg|png)(?:\?[^\s]*)?'
                            original_urls = re.findall(image_pattern, original_note, re.IGNORECASE)
                            # If we have URLs in original but processed text is different, 
                            # append URLs to the new text
                            if original_urls and processed_text != original_note:
                                return f"{processed_text} {' '.join(original_urls)}"
                    break
        
        # No existing URLs found, return processed text as-is
        return processed_text
    
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
                            
                            # White highlights (Akira white) - |text|
                            "highlight.white": Style(color="#ffffff", bold=True),
                            "highlight.white.content": Style(color="#ffffff", bold=True),
                            "highlight.white.bracket": Style(color="#ffffff", bold=True),
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
                    
                    
                    
                    highlights_list = ListView(id="highlights-list")
                    highlights_list.styles.background = "#1f1f39"
                    # Disable ListView's built-in selection behavior
                    highlights_list.can_focus = False
                    yield highlights_list
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Add visual feedback to all buttons
        self._add_button_press_feedback(event.button)
        
        # Track mark button clicks for delete functionality
        if event.button.id and event.button.id.startswith("mark-"):
            # Extract mark info from button ID and track it
            self._track_mark_click(event.button.id)
        
        if event.button.id == "next" and self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.save_current_page()  # Save page whenever it changes
        elif event.button.id == "prev" and self.current_page > 0:
            self.current_page -= 1
            self.save_current_page()  # Save page whenever it changes
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
        
        # Initialize new mark as collapsed (False)
        mark_key = self._get_mark_key(mark_data)
        self.mark_dropdown_states[mark_key] = False
        
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
        
        # Update the highlights list to show the new mark
        self.update_highlights_list()
        
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
    
    # PRESERVED DROPDOWN LOGIC - can be reused for future dropdown functionality
    # def toggle_dropdown(self, button_id: str) -> None:
    #     """Toggle a dropdown button to show/hide content."""
    #     highlights_list = self.query_one("#highlights-list", ListView)
    #     dropdown_button = self.query_one(f"#{button_id}", Button)
    #     
    #     # Check current visibility state by looking at the button text
    #     current_label = str(dropdown_button.label)
    #     is_expanded = current_label.endswith("▲")
    #     
    #     if is_expanded:
    #         # Currently expanded, so collapse
    #         dropdown_button.label = dropdown_button.label.replace("▲", "▼")
    #         # Hide content by clearing the list
    #         highlights_list.clear()
    #         debug_log(f"Collapsed {button_id} dropdown - cleared content")
    #     else:
    #         # Currently collapsed, so expand
    #         dropdown_button.label = dropdown_button.label.replace("▼", "▲")
    #         # Show content by updating the list
    #         self.update_highlights_list()
    #         debug_log(f"Expanded {button_id} dropdown - showing content")
    
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
        """Delete the highlight or mark based on the last interaction."""
        # Check if we should delete a mark or a note based on last interaction
        if self.last_interaction_type == 'mark' and self.last_clicked_mark:
            self._delete_mark(self.last_clicked_mark)
            return
        
        # Original note/highlight deletion logic
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
    
    def _track_mark_click(self, button_id: str) -> None:
        """Track when a mark button is clicked - handles both delete tracking and dropdown toggle."""
        # Find the mark data based on the button ID
        for mark in self.marks:
            if len(mark) == 6:
                page_num, start_row, start_col, selected_text, mark_name, timestamp = mark
                # Create the same sanitized ID that was used for the button
                mark_name_str = str(mark_name)
                sanitized_id = ''.join(c if c.isalnum() or c in '-_' else '-' for c in mark_name_str.lower())
                sanitized_id = '-'.join(filter(None, sanitized_id.split('-')))
                expected_button_id = f"mark-{sanitized_id}"
                
                if button_id == expected_button_id:
                    # Always track for delete functionality
                    self.last_clicked_mark = mark
                    self.last_interaction_type = 'mark'
                    
                    # Check if the button is disabled (no notes) - if so, don't toggle
                    try:
                        button = self.query_one(f"#{button_id}", Button)
                        if not button.disabled:
                            # Handle dropdown toggle only if button is not disabled
                            self._toggle_mark_dropdown(mark, button_id)
                            debug_log(f"Toggled mark dropdown: {mark_name} at page {page_num}")
                        else:
                            debug_log(f"Clicked disabled mark (no notes): {mark_name} at page {page_num}")
                    except Exception as e:
                        debug_log(f"Error checking button state: {e}")
                    break

    def _delete_mark(self, mark_to_delete) -> None:
        """Delete a specific mark from the marks list."""
        try:
            self.marks.remove(mark_to_delete)
            page_num, start_row, start_col, selected_text, mark_name, timestamp = mark_to_delete
            debug_log(f"Deleted mark '{mark_name}' from page {page_num}")
            
            # Clean up dropdown state for the deleted mark
            mark_key = self._get_mark_key(mark_to_delete)
            if mark_key in self.mark_dropdown_states:
                del self.mark_dropdown_states[mark_key]
            
            # Clear the last clicked mark since it's been deleted
            self.last_clicked_mark = None
            self.last_interaction_type = None
            
            # Save marks and update the display (this will restore previously hidden notes)
            self.save_marks()
            self.update_highlights_list()
            
        except ValueError:
            debug_log("Mark not found in marks list")
        except Exception as e:
            debug_log(f"Error deleting mark: {e}")

    def _is_mark_above_note(self, mark, note) -> bool:
        """Determine if a mark is 'above' a note (comes first when reading left-to-right)."""
        mark_page, mark_row, mark_col = mark[0], mark[1], mark[2]  # mark format: (page, row, col, text, name, timestamp)
        note_page, note_row, note_col = note[0], note[1], note[2]  # note format: (page, text, text, row, col, note_text, color)
        
        # Compare as tuples for proper ordering: (page, row, col)
        mark_pos = (mark_page, mark_row, mark_col)
        note_start_pos = (note_page, note_row, note_col)
        
        # Mark is above if its position comes before the note's start position
        return mark_pos < note_start_pos

    def _get_mark_key(self, mark) -> str:
        """Generate a unique key for a mark to track dropdown state."""
        page_num, start_row, start_col, selected_text, mark_name, timestamp = mark
        return f"mark_{page_num}_{start_row}_{start_col}_{timestamp}"

    def _count_notes_under_mark(self, mark, all_items) -> int:
        """Count how many notes are controlled by this mark."""
        mark_page, mark_row, mark_col = mark[0], mark[1], mark[2]
        mark_pos = (mark_page, mark_row, mark_col)
        
        # Find the next mark after this one
        next_mark_pos = None
        for item in all_items:
            if item[0] == 'mark':
                other_mark_page, other_mark_row, other_mark_col = item[1], item[2], item[3]
                other_mark_pos = (other_mark_page, other_mark_row, other_mark_col)
                
                # Skip the current mark itself
                if other_mark_pos == mark_pos:
                    continue
                    
                # Find first mark after current mark
                if other_mark_pos > mark_pos:
                    next_mark_pos = other_mark_pos
                    break
        
        # Count highlights that fall within this mark's scope
        note_count = 0
        for item in all_items:
            if item[0] == 'highlight':
                highlight_page, highlight_row, highlight_col = item[1], item[2], item[3]
                highlight_pos = (highlight_page, highlight_row, highlight_col)
                
                # Check if highlight is after this mark
                if highlight_pos > mark_pos:
                    # If there's a next mark, make sure highlight is before it
                    if next_mark_pos is None or highlight_pos < next_mark_pos:
                        note_count += 1
        
        return note_count

    def _toggle_mark_dropdown(self, mark, button_id: str) -> None:
        """Toggle the dropdown state of a mark and update button appearance."""
        mark_key = self._get_mark_key(mark)
        
        # Get current state (default to False/collapsed for new marks)
        is_expanded = self.mark_dropdown_states.get(mark_key, False)
        
        # Toggle the state
        new_state = not is_expanded
        self.mark_dropdown_states[mark_key] = new_state
        
        # Update button text to reflect new state
        try:
            # Instead of manually updating the label, refresh the entire list
            # This ensures the correct note count and arrow are shown
            self.update_highlights_list()
            
            mark_name = str(mark[4])  # mark_name is at index 4 in mark tuple
            if new_state:
                debug_log(f"Expanded mark: {mark_name}")
            else:
                debug_log(f"Collapsed mark: {mark_name}")
                
        except Exception as e:
            debug_log(f"Error updating mark button: {e}")

    def on_focus(self, event) -> None:
        """Track when TextAreas get focus for save/delete operations."""
        if (isinstance(event.widget, TextArea) and 
            hasattr(event.widget, 'id') and 
            event.widget.id and event.widget.id.startswith("note_")):
            self.last_focused_textarea = event.widget
            self.last_interaction_type = 'note'
            debug_log(f"Tracked focused textarea: {event.widget.id}")
    
    
    def update_highlight_color(self, page_num: int, start_row: int, start_col: int, new_color: str):
        """Update the color of a specific highlight."""
        if page_num in self.highlights:
            for i, highlight in enumerate(self.highlights[page_num]):
                start_pos, end_pos, text, note, color = parse_highlight_tuple(highlight)
                # Find the matching highlight by position
                if start_pos == (start_row, start_col):
                    # Strip existing brackets and rewrap with new color
                    clean_text = text.strip('[]{}()<>«»|')
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
                
                # If the note text is processed (URLs removed), we need to reconstruct 
                # the original note with URLs for proper storage
                final_note_text = self._reconstruct_note_with_urls(page_num, start_row, start_col, note_text)
                
                # Update the highlight with the note
                self.update_highlight_note(page_num, start_row, start_col, final_note_text)
                debug_log(f"Saved note for highlight at page {page_num}: {final_note_text}")
                
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
                manual_text = lines[start_row][start_col:end_col]
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
            clean_text = selected_text.strip('[]{}()<>«»|')
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
        
        # Process note text to hide image URLs but keep other text
        processed_note_text = note if note else ""
        if note:
            processed_note_text, _ = self.process_note_for_images(note)
        
        # Always create the editable TextArea
        # For server mode, we'll strip hyperlink markup for editing
        import sys
        is_server_mode = '--server' in sys.argv
        
        # Clean text for TextArea (remove markup)
        clean_text_for_editing = processed_note_text
        if is_server_mode and '[link=' in processed_note_text:
            # Remove markup but keep URLs visible
            import re
            clean_text_for_editing = re.sub(r'\[link=([^\]]+)\]([^\[]+)\[/link\]', r'\2', processed_note_text)
        
        note_area = TextArea(
            text=clean_text_for_editing,
            id=f"note_{page_num}_{start_row}_{start_col}",
            read_only=False
        )
        note_area.show_line_numbers = False
        
        # Process images and get the widgets to insert above the note
        image_widgets = self._get_image_widgets_for_note(note if note else "")
        
        # Create content layout
        content_widgets = [Label(display_text), note_area]
        
        # In server mode, add a clickable hyperlink display below the TextArea
        if is_server_mode and processed_note_text and '[link=' in processed_note_text:
            from textual.widgets import Static as RichStatic
            hyperlink_display = RichStatic(
                processed_note_text,
                markup=True,
                id=f"hyperlinks_{page_num}_{start_row}_{start_col}"
            )
            hyperlink_display.styles.margin = (1, 0, 0, 0)
            hyperlink_display.styles.padding = 1
            hyperlink_display.styles.background = "#2f2f49"
            hyperlink_display.styles.color = "#b3e3f2"
            hyperlink_display.styles.border = ("solid", "#9aa4ca")
            content_widgets.append(hyperlink_display)
        
        content = Vertical(*content_widgets)
        highlight_item = ListItem(content)
        
        # Store full data as metadata for note editing
        highlight_item.highlight_data = (page_num, full_text, start_row, start_col, note)
        return highlight_item, image_widgets
    
    def _get_image_widgets_for_note(self, note_text: str) -> list:
        """Process note text and return list of clickable image widgets."""
        image_widgets = []
        
        if not note_text:
            return image_widgets
            
        debug_log(f"Processing images for note: {note_text[:100]}...")
        processed_text, image_data = self.process_note_for_images(note_text)
        debug_log(f"Found {len(image_data)} images: {image_data}")
        
        # Create clickable image widgets for each downloaded image
        for url, image_path in image_data:
            try:
                debug_log(f"Creating clickable image widget for: {image_path} -> {url}")
                clickable_image = ClickableImage(image_path, url)
                clickable_image.add_class("note-image")
                image_widgets.append(clickable_image)
                debug_log(f"Successfully created clickable image widget")
                    
            except Exception as e:
                debug_log(f"Error creating clickable image widget: {e}")
                placeholder = Static(f"Error loading: {os.path.basename(image_path)}")
                placeholder.add_class("note-image")
                image_widgets.append(placeholder)
                
        return image_widgets
    
    def update_highlights_list(self) -> None:
        """Update the highlights ListView with marks and notes, respecting mark hierarchy."""
        highlights_list = self.query_one("#highlights-list", ListView)
        highlights_list.clear()
        
        # No need to clear separate image panel anymore
        
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
            all_items.append(('mark', page_num, start_row, start_col, selected_text, mark_name, mark))
        
        # Sort by position (page, row, col)
        all_items.sort(key=lambda x: (x[1], x[2], x[3]))
        
        # Apply mark hierarchy logic
        visible_items = self._apply_mark_hierarchy(all_items)
        
        # Create list items
        for item in visible_items:
            if item[0] == 'highlight':
                _, page_num, start_row, start_col, full_text, note, color = item
                highlight_item, image_widgets = self._create_highlight_list_item(
                    page_num, full_text, start_row, start_col, note, color
                )
                
                # Add image widgets first (they appear above the note)
                for image_widget in image_widgets:
                    image_list_item = ListItem(image_widget)
                    image_list_item.add_class("image-container")
                    highlights_list.append(image_list_item)
                
                # Then add the highlight item
                highlights_list.append(highlight_item)
            elif item[0] == 'mark':
                _, page_num, start_row, start_col, selected_text, mark_name, mark_data = item
                mark_item = self._create_mark_list_item(page_num, mark_name, selected_text, mark_data, all_items)
                highlights_list.append(mark_item)
        
        debug_log(f"Updated highlights list with {len(visible_items)} visible items ({len(all_highlights)} highlights, {len(self.marks)} marks)")
    
    def _apply_mark_hierarchy(self, all_items) -> list:
        """Apply mark hierarchy logic to determine which items should be visible."""
        visible_items = []
        
        for i, item in enumerate(all_items):
            item_type = item[0]
            
            if item_type == 'mark':
                # Marks are always visible
                visible_items.append(item)
            elif item_type == 'highlight':
                # Check if this highlight should be hidden by a mark
                should_hide = self._should_hide_highlight(item, all_items)
                if not should_hide:
                    visible_items.append(item)
                else:
                    debug_log(f"Hiding highlight at page {item[1]} row {item[2]} col {item[3]}")
        
        return visible_items
    
    def _should_hide_highlight(self, highlight_item, all_items) -> bool:
        """Determine if a highlight should be hidden based on mark hierarchy."""
        highlight_type, highlight_page, highlight_row, highlight_col = highlight_item[:4]
        highlight_pos = (highlight_page, highlight_row, highlight_col)
        
        # Find all marks that are "above" this highlight
        controlling_mark = None
        next_mark = None
        
        for item in all_items:
            if item[0] == 'mark':
                mark_page, mark_row, mark_col = item[1], item[2], item[3]
                mark_pos = (mark_page, mark_row, mark_col)
                
                if mark_pos < highlight_pos:
                    # This mark is above the highlight
                    controlling_mark = item
                elif mark_pos > highlight_pos:
                    # This is the first mark after the highlight
                    next_mark = item
                    break
        
        # If there's no controlling mark, highlight is visible
        if not controlling_mark:
            return False
            
        # If there's a controlling mark, check if it's expanded
        mark_data = controlling_mark[6]  # The full mark tuple
        if mark_data:
            mark_key = self._get_mark_key(mark_data)
            is_expanded = self.mark_dropdown_states.get(mark_key, False)
            
            # Hide if mark is collapsed (False), show if expanded (True)
            return not is_expanded
        
        return False
    
    def _create_mark_list_item(self, page_num: int, mark_name, selected_text: str, mark_data, all_items) -> ListItem:
        """Create a ListItem for a mark."""
        # Convert mark_name to string in case it's a timestamp or other type
        mark_name_str = str(mark_name)
        
        # Count notes under this mark
        note_count = self._count_notes_under_mark(mark_data, all_items)
        
        # Sanitize mark_name for use as ID: only allow letters, numbers, underscores, hyphens
        sanitized_id = ''.join(c if c.isalnum() or c in '-_' else '-' for c in mark_name_str.lower())
        # Remove consecutive hyphens and strip leading/trailing hyphens
        sanitized_id = '-'.join(filter(None, sanitized_id.split('-')))
        
        # Create button label based on whether it has notes
        if note_count > 0:
            # Get dropdown state to show correct arrow
            mark_key = self._get_mark_key(mark_data)
            is_expanded = self.mark_dropdown_states.get(mark_key, False)
            arrow = "▲" if is_expanded else "▼"
            button_label = f"{mark_name_str.upper()} ({note_count}) {arrow}"
        else:
            # No notes, no arrow
            button_label = f"{mark_name_str.upper()}"
        
        mark_button = Button(button_label, id=f"mark-{sanitized_id}")
        mark_button.can_focus = False
        mark_button.active_effect_duration = 0
        mark_button.styles.color = "#ffffff"
        mark_button.styles.width = "100%"
        mark_button.styles.text_align = "left"
        mark_button.styles.margin = (1, 0, 0, 0)
        
        # Disable button interaction if no notes
        if note_count == 0:
            mark_button.disabled = True
            mark_button.styles.color = "#666666"  # Dimmed color for disabled state
        
        # Create and return the ListItem with the button as content
        item = ListItem(mark_button)
        # Add mark-item class to remove borders via CSS
        item.add_class("mark-item")
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
                                clean_text = text.strip('[]{}()<>«»|')
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
        
        # Store saved page to load after mount (avoid reactive issues during init)
        self.saved_page_to_load = self._get_saved_page()
    
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
    
    def _parse_image_references(self, text: str) -> list:
        """Parse text for image URLs or references and return list of found images."""
        image_references = []
        
        # Regex patterns for different image reference formats
        patterns = [
            # URL patterns (http/https)
            r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp|svg)(?:\?[^\s]*)?',
            # Markdown image syntax ![alt](url)
            r'!\[[^\]]*\]\(([^\)]+\.(?:jpg|jpeg|png|gif|webp|svg)(?:\?[^\)]*)?)\)',
            # HTML image tags <img src="url">
            r'<img[^>]+src=["\']([^"\']+\.(?:jpg|jpeg|png|gif|webp|svg)(?:\?[^"\']*)?)["\'][^>]*>',
            # Simple file references (local files)
            r'[^\s]+\.(?:jpg|jpeg|png|gif|webp|svg)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if match.groups():
                    # Extract URL from capturing group (for markdown/html)
                    url = match.group(1)
                else:
                    # Use the full match (for direct URLs)
                    url = match.group(0)
                
                if url not in image_references:
                    image_references.append(url)
                    debug_log(f"Found image reference: {url}")
        
        return image_references


    def _create_image_widget(self, image_path: str):
        """Create a TextualImage widget for display."""
        if not TEXTUAL_IMAGE_AVAILABLE:
            return Static(f"[Image: {image_path}] (textual-image not available)")
        
        try:
            return TextualImage(image_path)
        except Exception as e:
            debug_log(f"Error creating image widget for {image_path}: {e}")
            return Static(f"[Image Error: {image_path}]")

    def _process_note_images(self, note_text: str) -> list:
        """Process a note's text and return list of image widgets for any found images."""
        image_widgets = []
        
        if not note_text:
            return image_widgets
        
        # Find image references in the note
        image_refs = self._parse_image_references(note_text)
        
        for img_ref in image_refs:
            # Check if it's a URL that needs downloading
            if img_ref.startswith(('http://', 'https://')):
                local_path = self.download_image(img_ref)
                if local_path:
                    widget = self._create_image_widget(local_path)
                    image_widgets.append(widget)
            else:
                # Local file reference
                if os.path.exists(img_ref):
                    widget = self._create_image_widget(img_ref)
                    image_widgets.append(widget)
                else:
                    debug_log(f"Local image file not found: {img_ref}")
        
        return image_widgets

    def save_current_page(self) -> None:
        """Save the current page number to a file."""
        try:
            with open('current_page.pkl', 'wb') as f:
                pickle.dump(self.current_page, f)
            debug_log(f"Saved current page: {self.current_page}")
        except Exception as e:
            debug_log(f"Error saving current page: {e}")

    def _get_saved_page(self) -> int:
        """Get the saved page number from a file without setting it."""
        try:
            with open('current_page.pkl', 'rb') as f:
                saved_page = pickle.load(f)
                # Ensure the saved page is within valid bounds
                if 0 <= saved_page < len(self.pages):
                    debug_log(f"Found saved page: {saved_page}")
                    return saved_page
                else:
                    debug_log(f"Saved page {saved_page} out of bounds, will start at page 0")
                    return 0
        except FileNotFoundError:
            debug_log("No current page file found, will start at page 0")
            return 0
        except Exception as e:
            debug_log(f"Error loading current page: {e}")
            return 0
    
    def on_mount(self) -> None:
        """Called when the app is mounted and ready."""
        # Set the current page now that DOM is ready
        if hasattr(self, 'saved_page_to_load'):
            self.current_page = self.saved_page_to_load
            debug_log(f"Set current page to: {self.current_page}")
        
        # Now that the UI is ready, update displays with loaded highlights
        if self.highlights:
            # Don't show highlights initially - let the dropdown control visibility
            self.apply_simple_highlighting()
        
        # Update the highlights list to show marks and highlights
        self.update_highlights_list()
        
        # Save current page on exit
        import atexit
        atexit.register(self.save_current_page)
        
        # Force override the ListView background after mounting
        try:
            highlights_list = self.query_one("#highlights-list", ListView)
            highlights_list.styles.background = "#1f1f39"
            highlights_list.refresh()
            debug_log("Forced ListView background override after mounting")
        except Exception as e:
            debug_log(f"Could not override ListView background: {e}")
        
        


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='GenreJinn EPUB Reader')
    parser.add_argument('--server', action='store_true', 
                       help='Run in server mode for web browser access')
    parser.add_argument('--host', default='127.0.0.1',
                       help='Host address for server mode (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8000,
                       help='Port for server mode (default: 8000)')
    parser.add_argument('--public-url', 
                       help='Public URL for server mode (e.g., https://blakelawyer.dev/genrejinn)')
    return parser.parse_args()

def run_server_mode(host, port, public_url=None):
    """Run the application in server mode using textual-serve."""
    if not TEXTUAL_SERVE_AVAILABLE:
        print("Error: textual-serve is not installed. Install it with: pip install textual-serve")
        return
    
    print(f"Starting GenreJinn server on {host}:{port}")
    if public_url:
        print(f"Public URL: {public_url}")
    
    # Create server with current script as command
    import sys
    server = Server(
        command=f'python {sys.argv[0]}',
        host=host,
        port=port,
        public_url=public_url
    )
    server.serve()

if __name__ == "__main__":
    args = parse_arguments()
    
    if args.server:
        # Run in server mode
        run_server_mode(args.host, args.port, args.public_url)
    else:
        # Run locally
        app = EPUBReader()
        app.run()
