import os
import ctypes
from tree_sitter import Language, Parser

def build_custom_language():
    """Build and load the custom language parser."""
    # For now, let's create a simple custom parser without tree-sitter
    # We'll implement our own basic parser for backtick-delimited highlights
    
    class CustomParser:
        def __init__(self):
            self.name = "custom"
        
        def parse(self, text):
            """Parse text and return highlight information."""
            highlights = []
            lines = text.split('\n')
            
            for line_num, line in enumerate(lines):
                in_highlight = False
                start_pos = None
                
                for char_pos, char in enumerate(line):
                    if char == '[' and not in_highlight:
                        # Start of highlight
                        start_pos = char_pos
                        in_highlight = True
                    elif char == ']' and in_highlight:
                        # End of highlight
                        if start_pos is not None:
                            content_text = line[start_pos + 1:char_pos]
                            full_text = line[start_pos:char_pos + 1]  # Include brackets
                            highlights.append({
                                'type': 'highlight',
                                'start_line': line_num,
                                'start_char': start_pos,
                                'end_line': line_num,
                                'end_char': char_pos + 1,  # Include closing bracket
                                'text': content_text,
                                'full_text': full_text
                            })
                        in_highlight = False
                        start_pos = None
            
            return highlights
        
        def get_syntax_styles(self, highlights):
            """Convert highlights to textual syntax styles."""
            styles = {}
            for highlight in highlights:
                # Create style entries for each highlight
                start = (highlight['start_line'], highlight['start_char'])
                end = (highlight['end_line'], highlight['end_char'] + 1)
                styles[(start, end)] = {
                    'color': '#fbdda7',  # Akira yellow
                    'bold': True
                }
            return styles
    
    return CustomParser()

# Create global instance
custom_language = build_custom_language()