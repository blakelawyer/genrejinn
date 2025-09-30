"""Syntax highlighting module for GenreJinn EPUB reader.

This module provides tree-sitter based syntax highlighting for multi-color
text annotations in EPUB content.
"""

from .manager import HighlightManager
from .custom_language import get_custom_language

__all__ = ['HighlightManager', 'get_custom_language']