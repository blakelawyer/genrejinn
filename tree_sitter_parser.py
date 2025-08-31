#!/usr/bin/env python3
"""Real tree-sitter parser using the compiled custom grammar."""

import ctypes
from pathlib import Path
from tree_sitter import Language, Parser, Node


class CustomTreeSitterParser:
    """Tree-sitter parser for bracket-delimited highlights."""
    
    def __init__(self):
        # Load the compiled language library
        lib_path = Path("build/custom.so")
        if not lib_path.exists():
            raise FileNotFoundError(f"Library not found: {lib_path}")
        
        # Load the shared library
        lib = ctypes.CDLL(str(lib_path))
        
        # Get the language function
        lib.tree_sitter_custom.restype = ctypes.c_void_p
        language_fn = lib.tree_sitter_custom
        
        # Create the Language object
        self.language = Language(language_fn())
        
        # Create parser
        self.parser = Parser()
        self.parser.language = self.language
        
        # Define the highlight query for TextArea
        self.highlight_query = """
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
    
    def parse(self, text: str):
        """Parse text and return highlight information."""
        # Parse the text
        tree = self.parser.parse(bytes(text, "utf8"))
        
        # Extract highlights
        highlights = []
        
        def traverse_node(node: Node):
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
    
    def get_syntax_styles(self, highlights):
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


# Create global instance
try:
    tree_sitter_language = CustomTreeSitterParser()
    print("Tree-sitter parser loaded successfully!")
except Exception as e:
    print(f"Failed to load tree-sitter parser: {e}")
    # Fallback to the simple parser
    from custom_parser import custom_language
    tree_sitter_language = custom_language