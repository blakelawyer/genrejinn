# Development Tools

This directory contains development and testing utilities for GenreJinn.

## Scripts

### `build_grammar.py`
Builds the custom tree-sitter grammar for multi-color highlighting.

**Usage:**
```bash
cd /path/to/genrejinn
python dev/build_grammar.py
```

This compiles the grammar from `tree-sitter-custom/grammar.js` and outputs the compiled library to `syntax/grammars/custom/compiled/custom.so`.

### `test_image.py`
Tests image display libraries (textual-image, textual-imageview) for potential future image support in the EPUB reader.

**Usage:**
```bash
python dev/test_image.py
```

## Requirements

- GCC compiler for building tree-sitter grammars
- tree-sitter CLI tool for generating parsers (if modifying grammar)