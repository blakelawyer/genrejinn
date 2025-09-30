"""EPUB parsing and content management."""

from .parser import EPUBParser
from .pagination import EPUBPaginator

__all__ = ["EPUBParser", "EPUBPaginator"]