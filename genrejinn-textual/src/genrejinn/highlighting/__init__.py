"""Multi-color highlighting system with tree-sitter support."""

from .manager import HighlightManager
from .colors import ColorManager
from .tree_sitter import TreeSitterHighlighter

__all__ = ["HighlightManager", "ColorManager", "TreeSitterHighlighter"]