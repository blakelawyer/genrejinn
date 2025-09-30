#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""EPUB file parsing and content extraction."""

import zipfile
import re
import os
from pathlib import Path


class EPUBParser:
    """Parser for extracting content from EPUB files."""

    def __init__(self, epub_path: str = None):
        self.epub_path = epub_path or self._get_default_epub_path()

    def _get_default_epub_path(self) -> str:
        """Get the default EPUB file path."""
        return 'data/bookshelf/gravitys-rainbow.epub'

    def load_paragraphs(self) -> list:
        """Load paragraphs from EPUB file."""
        if not os.path.exists(self.epub_path):
            raise FileNotFoundError(f"EPUB file not found: {self.epub_path}")

        with zipfile.ZipFile(self.epub_path, 'r') as epub_file:
            html_files = [f for f in epub_file.namelist() if f.endswith('.html') and 'text' in f]
            html_files.sort()

            all_paragraphs = []
            for filename in html_files:
                content = epub_file.read(filename).decode('utf-8', errors='ignore')
                para_matches = re.findall(r'<p[^>]*>(.*?)</p>', content, re.DOTALL | re.IGNORECASE)

                for para_html in para_matches:
                    para_text = re.sub(r'<[^>]+>', '', para_html)
                    para_text = re.sub(r'\s+', ' ', para_text).strip()

                    if para_text:
                        all_paragraphs.append(para_text)

        return all_paragraphs

    def get_book_info(self) -> dict:
        """Extract book metadata from EPUB file."""
        # This could be expanded to parse OPF files for metadata
        return {
            'title': os.path.basename(self.epub_path).replace('.epub', '').replace('-', ' ').title(),
            'path': self.epub_path,
            'size': os.path.getsize(self.epub_path) if os.path.exists(self.epub_path) else 0
        }