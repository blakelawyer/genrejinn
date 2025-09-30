"""Highlight manager for tree-sitter syntax highlighting."""

from pathlib import Path
from tree_sitter import Parser
from .custom_language import get_custom_language

class HighlightManager:
    """Tree-sitter parser for bracket-delimited highlights."""
    
    def __init__(self):
        # Load the custom language
        self.language = get_custom_language()
        
        # Create parser
        self.parser = Parser()
        self.parser.language = self.language
        
        # Load highlight query from file
        self.highlight_query = self._load_highlight_query()
    
    def _load_highlight_query(self) -> str:
        """Load highlight query from the grammar directory."""
        query_path = Path(__file__).parent / "grammars" / "custom" / "queries" / "highlights.scm"
        if query_path.exists():
            return query_path.read_text()
        else:
            # Fallback inline query
            return """
            (yellow_highlight) @highlight.yellow
            (yellow_content) @highlight.yellow.content
            "[" @highlight.yellow.bracket
            "]" @highlight.yellow.bracket

            (green_highlight) @highlight.green
            (green_content) @highlight.green.content
            "{" @highlight.green.bracket
            "}" @highlight.green.bracket

            (red_highlight) @highlight.red
            (red_content) @highlight.red.content
            "<" @highlight.red.bracket
            ">" @highlight.red.bracket

            (blue_highlight) @highlight.blue
            (blue_content) @highlight.blue.content
            "«" @highlight.blue.bracket
            "»" @highlight.blue.bracket

            (white_highlight) @highlight.white
            (white_content) @highlight.white.content
            "⟨" @highlight.white.bracket
            "⟩" @highlight.white.bracket
            """
    
    def parse(self, text: str) -> list:
        """Parse text and return highlight information."""
        if not self.language:
            return []
            
        # Parse the text
        tree = self.parser.parse(bytes(text, "utf8"))
        
        # Extract highlights
        highlights = []
        
        def traverse_node(node):
            """Recursively traverse the syntax tree."""
            if node.type == "highlighted_text":
                # Get the position info
                start_point = node.start_point
                end_point = node.end_point
                
                # Find the content node (excluding brackets)
                content_node = None
                for child in node.children:
                    if child.type == "highlight_content":
                        content_node = child
                        break
                
                if content_node:
                    content_text = text[content_node.start_byte:content_node.end_byte]
                    highlights.append({
                        'type': 'highlight',
                        'start_line': start_point.row,
                        'start_char': start_point.column,
                        'end_line': end_point.row,
                        'end_char': end_point.column,
                        'text': content_text,
                        'full_text': text[node.start_byte:node.end_byte]  # Including brackets
                    })
            
            # Recurse to children
            for child in node.children:
                traverse_node(child)
        
        traverse_node(tree.root_node)
        return highlights
    
    def get_syntax_styles(self, highlights) -> dict:
        """Convert highlights to textual syntax styles."""
        styles = {}
        for highlight in highlights:
            # Create style entries for each highlight
            start = (highlight['start_line'], highlight['start_char'])
            end = (highlight['end_line'], highlight['end_char'])
            styles[(start, end)] = {
                'color': '#fbdda7',  # Akira yellow
                'bold': True
            }
        return styles


# Create a compatibility object that matches the old interface
class TreeSitterLanguage:
    """Compatibility wrapper for the old tree_sitter_language interface."""
    
    def __init__(self):
        self.manager = HighlightManager()
        self.language = self.manager.language
        self.highlight_query = self.manager.highlight_query


# Create global instance for backward compatibility
try:
    tree_sitter_language = TreeSitterLanguage()
    print("Tree-sitter parser loaded successfully!")
except Exception as e:
    print(f"Failed to load tree-sitter parser: {e}")
    tree_sitter_language = None