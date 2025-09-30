#!/usr/bin/env python3
"""Build the tree-sitter custom language parser."""

import os
import shutil
import subprocess
from pathlib import Path

def build_tree_sitter_language():
    """Build the tree-sitter language using the C compiler."""
    
    # Paths relative to the project root (one level up from dev/)
    project_root = Path(__file__).parent.parent
    grammar_dir = project_root / "tree-sitter-custom"
    compiled_dir = project_root / "syntax" / "grammars" / "custom" / "compiled"
    
    # Create compiled directory
    compiled_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for parser.c file
    parser_c = grammar_dir / "src" / "parser.c"
    if not parser_c.exists():
        raise FileNotFoundError(f"Parser file not found: {parser_c}. Run 'tree-sitter generate' first.")
    
    # Compile the shared library
    lib_path = compiled_dir / "custom.so"
    
    cmd = [
        "gcc",
        "-shared",
        "-fPIC",
        "-I", str(grammar_dir / "src"),
        str(parser_c),
        "-o", str(lib_path)
    ]
    
    print(f"Building library: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    
    print(f"Successfully built {lib_path}")
    return lib_path

if __name__ == "__main__":
    build_tree_sitter_language()