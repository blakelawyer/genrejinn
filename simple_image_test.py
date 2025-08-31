#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

# Try different image display libraries
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


class SimpleImageApp(App):
    CSS = """
    Screen {
        background: #1f1f39;
    }
    
    Static {
        background: #1f1f39;
        color: #9aa4ca;
        margin: 1;
        padding: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Simple Image Display Test", id="title")
            
            # Show status
            status_text = f"textual-image: {'✓' if TEXTUAL_IMAGE_AVAILABLE else '✗'}\n"
            status_text += f"textual-imageview: {'✓' if IMAGEVIEW_AVAILABLE else '✗'}\n"
            yield Static(status_text, id="status")
            
            # Try to display sample.png directly
            try:
                if TEXTUAL_IMAGE_AVAILABLE:
                    yield TextualImage("sample.png")
                    yield Static("Using textual-image")
                elif IMAGEVIEW_AVAILABLE:
                    yield ImageViewer("sample.png")
                    yield Static("Using textual-imageview")
                else:
                    yield Static("No image libraries available")
            except Exception as e:
                yield Static(f"Error loading image: {e}")


if __name__ == "__main__":
    app = SimpleImageApp()
    app.run()