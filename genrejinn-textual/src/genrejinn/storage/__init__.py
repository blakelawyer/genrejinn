"""Data persistence and storage management."""

from .highlights import HighlightStorage
from .marks import MarkStorage
from .images import ImageManager
from .page_state import PageStateManager

__all__ = ["HighlightStorage", "MarkStorage", "ImageManager", "PageStateManager"]