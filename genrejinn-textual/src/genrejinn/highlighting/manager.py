#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Highlight management and application logic."""

from .colors import ColorManager, parse_highlight_tuple


class HighlightManager:
    """Manage highlights for the EPUB reader."""

    def __init__(self):
        self.highlights = {}  # {page_number: [(start_pos, end_pos, text, note, color), ...]}
        self.current_color_index = 0
        self.highlight_colors = ColorManager.get_highlight_colors()

    def cycle_color(self) -> tuple:
        """Cycle through colors and return (name, hex)."""
        self.current_color_index = (self.current_color_index + 1) % len(self.highlight_colors)
        return self.highlight_colors[self.current_color_index]

    def get_current_color(self) -> tuple:
        """Get current color (name, hex)."""
        return self.highlight_colors[self.current_color_index]

    def add_highlight(self, page_num: int, start_pos: tuple, end_pos: tuple,
                     selected_text: str, note: str = "") -> None:
        """Add a highlight to the specified page."""
        if page_num not in self.highlights:
            self.highlights[page_num] = []

        # Get current selected color and convert to full name
        color_name, _ = self.get_current_color()
        full_color_name = ColorManager.get_full_color_name(color_name)

        # Wrap text with color brackets
        bracketed_text = ColorManager.wrap_text_with_color(selected_text, full_color_name)

        highlight_data = (start_pos, end_pos, bracketed_text, note, full_color_name)
        self.highlights[page_num].append(highlight_data)

    def update_highlight_note(self, page_num: int, start_row: int, start_col: int, note_text: str) -> bool:
        """Update the note for a specific highlight."""
        if note_text == "DELETE":
            return self._delete_highlight(page_num, start_row, start_col)

        # Find and update the highlight with the note
        if page_num in self.highlights:
            for i, highlight in enumerate(self.highlights[page_num]):
                start_pos, end_pos, text, old_note, color = parse_highlight_tuple(highlight)
                if start_pos == (start_row, start_col):
                    # Update the highlight with the new note (preserve color info)
                    if len(highlight) == 4:
                        self.highlights[page_num][i] = (start_pos, end_pos, text, note_text, "yellow")
                    else:
                        self.highlights[page_num][i] = (start_pos, end_pos, text, note_text, color)
                    return True
        return False

    def _delete_highlight(self, page_num: int, start_row: int, start_col: int) -> bool:
        """Delete a specific highlight."""
        if page_num in self.highlights:
            original_count = len(self.highlights[page_num])
            self.highlights[page_num] = [
                highlight
                for highlight in self.highlights[page_num]
                if (highlight[0] if len(highlight) >= 1 else None) != (start_row, start_col)
            ]
            # Remove the page entry if no highlights remain
            if not self.highlights[page_num]:
                del self.highlights[page_num]

            return len(self.highlights.get(page_num, [])) < original_count
        return False

    def update_highlight_color(self, page_num: int, start_row: int, start_col: int, new_color: str) -> bool:
        """Update the color of a specific highlight."""
        if page_num in self.highlights:
            for i, highlight in enumerate(self.highlights[page_num]):
                start_pos, end_pos, text, note, color = parse_highlight_tuple(highlight)
                # Find the matching highlight by position
                if start_pos == (start_row, start_col):
                    # Strip existing brackets and rewrap with new color
                    clean_text = ColorManager.strip_brackets(text, color)
                    new_text = ColorManager.wrap_text_with_color(clean_text, new_color)

                    # Update the highlight data
                    self.highlights[page_num][i] = (start_pos, end_pos, new_text, note, new_color)
                    return True
        return False

    def apply_highlights_to_text(self, page_num: int, original_text: str) -> str:
        """Apply highlighting brackets to text for the specified page."""
        if page_num not in self.highlights or not self.highlights[page_num]:
            return original_text

        highlighted_text = original_text
        # Sort highlights by position (reverse order to avoid position shifts)
        sorted_highlights = sorted(self.highlights[page_num], key=lambda h: h[0], reverse=True)

        for highlight in sorted_highlights:
            _, _, selected_text, note, color = parse_highlight_tuple(highlight)
            # The text already has proper color brackets, use as-is
            highlighted_version = selected_text

            # Extract the text without brackets for replacement
            clean_text = ColorManager.strip_brackets(selected_text, color)
            highlighted_text = highlighted_text.replace(clean_text, highlighted_version)

        return highlighted_text

    def get_all_highlights(self) -> list:
        """Get all highlights from all pages, sorted by position."""
        all_highlights = []
        for page_num, page_highlights in self.highlights.items():
            for highlight in page_highlights:
                start_pos, end_pos, text, note, color = parse_highlight_tuple(highlight)
                start_row, start_col = start_pos
                all_highlights.append((page_num, text, text, start_row, start_col, note, color))

        # Sort highlights by page number, then by position in text
        all_highlights.sort(key=lambda x: (x[0], x[3], x[4]))  # page, start_row, start_col
        return all_highlights

    def get_page_highlights(self, page_num: int) -> list:
        """Get highlights for a specific page."""
        return self.highlights.get(page_num, [])