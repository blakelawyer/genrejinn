#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Color management system for highlights."""


class ColorManager:
    """Centralized color management for highlights."""

    # 3-character codes to full color names
    COLOR_MAPPING = {
        "yel": "yellow",
        "red": "red",
        "grn": "green",
        "blu": "blue",
        "wht": "white"
    }

    # Color brackets for text wrapping
    COLOR_BRACKETS = {
        "yellow": ("[", "]"),
        "green": ("{", "}"),
        "red": ("<", ">"),
        "blue": ("«", "»"),
        "white": ("⟨", "⟩")
    }

    # Color hex values for display (Akira color scheme)
    COLOR_HEX = {
        "yellow": "#fbdda7",
        "red": "#ff6a6e",
        "green": "#6be28d",
        "blue": "#b3e3f2",
        "white": "#ffffff"
    }

    @classmethod
    def get_full_color_name(cls, short_name: str) -> str:
        """Convert 3-char code to full color name."""
        return cls.COLOR_MAPPING.get(short_name.lower(), "yellow")

    @classmethod
    def get_brackets(cls, color: str) -> tuple:
        """Get open/close brackets for a color."""
        return cls.COLOR_BRACKETS.get(color, ("[", "]"))

    @classmethod
    def get_hex(cls, color: str) -> str:
        """Get hex value for a color."""
        return cls.COLOR_HEX.get(color, "#fbdda7")

    @classmethod
    def strip_brackets(cls, text: str, color: str) -> str:
        """Strip bracket characters from highlighted text to get clean content."""
        if not text or color not in cls.COLOR_BRACKETS:
            return text

        open_bracket, close_bracket = cls.COLOR_BRACKETS[color]

        # Remove opening bracket if text starts with it
        if text.startswith(open_bracket):
            text = text[len(open_bracket):]

        # Remove closing bracket if text ends with it
        if text.endswith(close_bracket):
            text = text[:-len(close_bracket)]

        return text

    @classmethod
    def wrap_text_with_color(cls, text: str, color: str) -> str:
        """Wrap text with color brackets."""
        open_bracket, close_bracket = cls.get_brackets(color)
        return f"{open_bracket}{text}{close_bracket}"

    @classmethod
    def get_highlight_colors(cls) -> list:
        """Get list of (name, hex) tuples for UI cycling."""
        return [
            ("YEL", cls.COLOR_HEX["yellow"]),
            ("RED", cls.COLOR_HEX["red"]),
            ("GRN", cls.COLOR_HEX["green"]),
            ("BLU", cls.COLOR_HEX["blue"]),
            ("WHT", cls.COLOR_HEX["white"])
        ]


def parse_highlight_tuple(highlight: tuple) -> tuple:
    """Parse highlight tuple handling both old (4-element) and new (5-element) formats.

    Returns: (start_pos, end_pos, text, note, color)
    """
    if len(highlight) == 4:
        start_pos, end_pos, text, note = highlight
        return start_pos, end_pos, text, note, "yellow"
    else:
        return highlight  # Already 5 elements