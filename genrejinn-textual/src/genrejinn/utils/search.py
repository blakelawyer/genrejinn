#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Search functionality for GenreJinn."""


def debug_log(message):
    """Debug logging function."""
    with open('data/log.txt', 'a') as f:
        f.write(f"{message}\n")
        f.flush()


class SearchEngine:
    """Handle full-text search across EPUB pages."""

    def __init__(self):
        self.search_term = ""
        self.search_matches = []  # List of (page_number, line_num, col_num, match_position) tuples
        self.current_search_index = -1

    def perform_search(self, search_term: str, pages: list) -> int:
        """Perform search across all pages and store results. Returns number of matches found."""
        if not search_term.strip():
            self.clear_search()
            return 0

        self.search_term = search_term.lower()
        self.search_matches = []
        self.current_search_index = -1

        # Search through all pages
        for page_num, page_content in enumerate(pages):
            page_lower = page_content.lower()
            # Find all matches on this page
            start_pos = 0
            while True:
                match_pos = page_lower.find(self.search_term, start_pos)
                if match_pos == -1:
                    break

                # Convert byte position to line and column
                lines = page_content[:match_pos].split('\n')
                line_num = len(lines) - 1
                col_num = len(lines[-1])

                self.search_matches.append((page_num, line_num, col_num, match_pos))
                start_pos = match_pos + 1

        debug_log(f"Search for '{search_term}' found {len(self.search_matches)} matches")

        # Set to first match if any found
        if self.search_matches:
            self.current_search_index = 0

        return len(self.search_matches)

    def next_match(self) -> tuple:
        """Navigate to the next search match. Returns (page_num, line_num, col_num) or None."""
        if not self.search_matches:
            return None

        self.current_search_index = (self.current_search_index + 1) % len(self.search_matches)
        return self.get_current_match()

    def prev_match(self) -> tuple:
        """Navigate to the previous search match. Returns (page_num, line_num, col_num) or None."""
        if not self.search_matches:
            return None

        self.current_search_index = (self.current_search_index - 1) % len(self.search_matches)
        return self.get_current_match()

    def get_current_match(self) -> tuple:
        """Get the current search match. Returns (page_num, line_num, col_num) or None."""
        if not self.search_matches or self.current_search_index < 0:
            return None

        match_data = self.search_matches[self.current_search_index]
        return match_data[:3]  # page_num, line_num, col_num

    def get_match_info(self) -> dict:
        """Get information about current search state."""
        return {
            'term': self.search_term,
            'total_matches': len(self.search_matches),
            'current_index': self.current_search_index + 1 if self.current_search_index >= 0 else 0,
            'has_matches': len(self.search_matches) > 0
        }

    def clear_search(self) -> None:
        """Clear search results and reset state."""
        self.search_term = ""
        self.search_matches = []
        self.current_search_index = -1

    def get_selection_bounds(self) -> tuple:
        """Get the start and end positions for highlighting the current match."""
        if not self.search_matches or self.current_search_index < 0:
            return None

        page_num, line_num, col_num, _ = self.search_matches[self.current_search_index]
        start_pos = (line_num, col_num)
        end_pos = (line_num, col_num + len(self.search_term))
        return start_pos, end_pos