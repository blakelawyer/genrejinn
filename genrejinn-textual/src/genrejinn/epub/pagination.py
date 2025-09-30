#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""EPUB content pagination logic."""


class EPUBPaginator:
    """Handle pagination of EPUB content."""

    def __init__(self, total_pages: int = 776):
        self.total_pages = total_pages

    def create_pages(self, paragraphs: list) -> list:
        """Group paragraphs into pages."""
        if not paragraphs:
            return []

        pages = []
        total_paragraphs = len(paragraphs)
        paragraphs_per_page = total_paragraphs // self.total_pages
        extra_paragraphs = total_paragraphs % self.total_pages

        start_index = 0
        for page_num in range(self.total_pages):
            # Some pages get one extra paragraph to distribute the remainder
            page_size = paragraphs_per_page + (1 if page_num < extra_paragraphs else 0)

            if start_index >= total_paragraphs:
                # If we run out of paragraphs, create empty pages
                pages.append("")
            else:
                end_index = min(start_index + page_size, total_paragraphs)
                page_paragraphs = paragraphs[start_index:end_index]
                pages.append('\n\n'.join(page_paragraphs))
                start_index = end_index

        return pages

    def get_page_info(self, current_page: int) -> dict:
        """Get information about a specific page."""
        return {
            'current': current_page + 1,
            'total': self.total_pages,
            'progress': (current_page + 1) / self.total_pages,
            'percentage': round(((current_page + 1) / self.total_pages) * 100, 1)
        }