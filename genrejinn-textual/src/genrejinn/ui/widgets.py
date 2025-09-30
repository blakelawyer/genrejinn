#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Custom UI widgets for GenreJinn."""

import os
import webbrowser
from textual.containers import Vertical
from textual.widgets import Static
from textual.events import Click

# Try to import image widgets
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


def debug_log(message):
    """Debug logging function."""
    with open('data/log.txt', 'a') as f:
        f.write(f"{message}\n")
        f.flush()


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

    def compose(self):
        yield self.image_widget

    def on_click(self, event: Click) -> None:
        """Open the image URL in browser when clicked."""
        debug_log(f"Image clicked, opening URL: {self.image_url}")
        try:
            webbrowser.open(self.image_url)
        except Exception as e:
            debug_log(f"Error opening URL: {e}")


def create_image_widget(image_path: str):
    """Create an image widget for display."""
    if not TEXTUAL_IMAGE_AVAILABLE:
        return Static(f"[Image: {image_path}] (textual-image not available)")

    try:
        return TextualImage(image_path)
    except Exception as e:
        debug_log(f"Error creating image widget for {image_path}: {e}")
        return Static(f"[Image Error: {image_path}]")