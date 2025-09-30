"""Custom tree-sitter language for highlight bracket parsing."""

import ctypes
from tree_sitter import Language
from pathlib import Path

def get_custom_language():
    """Get the compiled custom tree-sitter language."""
    # Get the path to the compiled library
    current_dir = Path(__file__).parent
    lib_path = current_dir / "grammars" / "custom" / "compiled" / "custom.so"
    
    if not lib_path.exists():
        raise FileNotFoundError(
            f"Compiled grammar not found at {lib_path}. "
            "Run dev/build_grammar.py to build the grammar."
        )
    
    # Load the shared library and get the language function
    lib = ctypes.CDLL(str(lib_path))
    lib.tree_sitter_custom.restype = ctypes.c_void_p
    language_fn = lib.tree_sitter_custom
    
    # Create the Language object
    return Language(language_fn())

# Create the language instance for easy import
try:
    custom_language = get_custom_language()
except FileNotFoundError as e:
    print(f"Warning: {e}")
    custom_language = None