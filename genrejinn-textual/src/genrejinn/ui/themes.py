#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""UI themes and styling for GenreJinn."""


class AkiraTheme:
    """Akira color scheme constants and CSS generation."""

    # Akira Color Scheme
    COLORS = {
        'background': '#1f1f39',
        'foreground': '#9aa4ca',
        'white': '#ffffff',
        'red': '#ff6a6e',
        'green': '#6be28d',
        'blue': '#b3e3f2',
        'yellow': '#fbdda7'
    }

    @classmethod
    def get_main_css(cls) -> str:
        """Get the main CSS for the application."""
        return f"""
        Screen {{
            background: {cls.COLORS['background']};
        }}

        #main-content {{
            height: 100vh;
        }}

        #left-panel {{
            width: 50%;
        }}

        TextArea {{
            background: {cls.COLORS['background']};
            color: {cls.COLORS['foreground']};
            margin: 1;
            padding: 1;
            border: solid {cls.COLORS['foreground']};
        }}

        #left-controls {{
            height: auto;
            min-height: 5;
            background: {cls.COLORS['background']};
            border: solid {cls.COLORS['foreground']};
            margin: 0 1 1 1;
            padding: 1;
            min-width: 0;
        }}

        #notes-panel {{
            width: 50%;
            margin: 1;
            padding: 1;
            border: solid {cls.COLORS['foreground']};
            background: {cls.COLORS['background']};
            color: {cls.COLORS['white']};
            height: 100%;
        }}

        #notes-title {{
            text-align: center;
            color: {cls.COLORS['foreground']};
            background: {cls.COLORS['background']};
            margin-bottom: 1;
        }}

        #highlights-list {{
            background: {cls.COLORS['background']};
            color: {cls.COLORS['white']};
            height: 1fr;
        }}

        ListView {{
            background: {cls.COLORS['background']};
        }}

        ListItem {{
            background: {cls.COLORS['background']};
            color: {cls.COLORS['white']};
            padding: 1;
            margin: 0 0 1 0;
            border: solid {cls.COLORS['foreground']} 50%;
            height: auto;
        }}

        ListItem:hover {{
            background: #2f2f49;
        }}

        /* Mark items without borders */
        ListItem.mark-item {{
            border: none;
            padding: 0;
            margin: 0;
        }}

        ListItem > Label {{
            color: {cls.COLORS['white']};
            background: transparent;
            text-wrap: wrap;
            width: 100%;
            height: auto;
        }}

        #note-input {{
            background: #2f2f49;
            color: {cls.COLORS['foreground']};
            border: solid {cls.COLORS['foreground']};
            margin: 1 0;
            padding: 1;
            height: 5;
            visibility: hidden;
        }}

        .hidden {{
            display: none;
        }}

        Button {{
            min-width: 4;
            margin: 0 1;
            background: {cls.COLORS['background']};
            border: solid {cls.COLORS['foreground']};
            color: {cls.COLORS['foreground']};
        }}

        #text-area {{
            height: 1fr;
        }}

        #left-controls {{
            height: auto;
            align: center middle;
        }}

        #left-controls > Horizontal {{
            width: 100%;
            align: center middle;
            margin-bottom: 1;
            height: auto;
        }}

        #progress {{
            width: auto;
            min-width: 0;
            margin: 1 1 0 1;
            text-align: center;
        }}

        #prev, #next {{
            width: auto;
            min-width: 4;
            max-width: 8;
        }}

        #counter {{
            text-align: center;
            margin: 0;
            color: {cls.COLORS['white']} !important;
        }}

        Static#counter {{
            color: {cls.COLORS['white']} !important;
        }}

        /* Button text colors */
        #highlight {{
            color: {cls.COLORS['blue']};
        }}

        #save-note {{
            color: {cls.COLORS['green']};
        }}

        #delete-highlight {{
            color: {cls.COLORS['red']};
        }}

        #prev, #next {{
            color: {cls.COLORS['yellow']};
        }}

        #color-button {{
            color: {cls.COLORS['foreground']};
            min-width: 11;
            text-align: center;
        }}

        #color-button:focus {{
            background: {cls.COLORS['background']} !important;
            border: solid {cls.COLORS['foreground']} !important;
            outline: none !important;
        }}

        #color-button:hover {{
            background: {cls.COLORS['background']};
        }}

        #prev:focus, #next:focus, #highlight:focus, #save-note:focus, #delete-highlight:focus {{
            background: {cls.COLORS['background']} !important;
            border: solid {cls.COLORS['foreground']} !important;
            outline: none !important;
        }}

        #prev:hover, #next:hover, #highlight:hover, #save-note:hover, #delete-highlight:hover {{
            background: {cls.COLORS['background']};
        }}

        #highlight-controls {{
            height: auto;
            align: center middle;
        }}

        #search-controls {{
            height: auto;
            align: center middle;
            margin-top: 1;
        }}

        #search-input {{
            width: 1fr;
            margin-right: 1;
        }}

        #counter {{
            text-align: center;
            width: 1fr;
            color: {cls.COLORS['foreground']};
            background: {cls.COLORS['background']};
        }}

        #notes-title {{
            color: {cls.COLORS['white']};
            text-style: bold;
        }}

        ProgressBar {{
            background: {cls.COLORS['background']};
            color: {cls.COLORS['foreground']};
        }}

        /* Style the actual Bar widget inside ProgressBar */
        Bar > .bar--bar {{
            color: {cls.COLORS['green']};
            background: {cls.COLORS['red']};
        }}

        Bar > .bar--complete {{
            color: {cls.COLORS['yellow']};
            background: {cls.COLORS['red']};
        }}

        /* TextArea inside ListView items */
        ListView ListItem TextArea {{
            height: auto;
            min-height: 3;
            border: none;
            margin: 0;
            padding: 1;
            background: {cls.COLORS['background']};
            color: {cls.COLORS['foreground']};
            overflow-y: hidden;
        }}

        /* Ensure ListView items have proper sizing */
        ListView ListItem {{
            height: auto;
            min-height: 5;
            padding: 1;
        }}

        /* Disable hover highlighting on ListView items */
        ListView ListItem:hover {{
            background: {cls.COLORS['background']};
        }}

        /* Scrollbar styling */
        TextArea {{
            scrollbar-background: {cls.COLORS['background']};
            scrollbar-background-active: {cls.COLORS['background']};
            scrollbar-background-hover: {cls.COLORS['background']};
            scrollbar-color: {cls.COLORS['foreground']};
            scrollbar-color-active: {cls.COLORS['foreground']};
            scrollbar-color-hover: {cls.COLORS['foreground']};
            scrollbar-corner-color: {cls.COLORS['background']};
        }}

        ListView {{
            scrollbar-background: {cls.COLORS['background']};
            scrollbar-background-active: {cls.COLORS['background']};
            scrollbar-background-hover: {cls.COLORS['background']};
            scrollbar-color: {cls.COLORS['foreground']};
            scrollbar-color-active: {cls.COLORS['foreground']};
            scrollbar-color-hover: {cls.COLORS['foreground']};
            scrollbar-corner-color: {cls.COLORS['background']};
        }}

        /* Apply to all widgets with scrollbars */
        * {{
            scrollbar-background: {cls.COLORS['background']};
            scrollbar-background-active: {cls.COLORS['background']};
            scrollbar-background-hover: {cls.COLORS['background']};
            scrollbar-color: {cls.COLORS['foreground']};
            scrollbar-color-active: {cls.COLORS['foreground']};
            scrollbar-color-hover: {cls.COLORS['foreground']};
            scrollbar-corner-color: {cls.COLORS['background']};
        }}

        /* Mark input field styling */
        #mark-input {{
            background: {cls.COLORS['background']};
            color: {cls.COLORS['foreground']};
            border: solid {cls.COLORS['foreground']};
            margin-bottom: 1;
        }}

        /* Image widget styling for ListView items */
        .note-image {{
            height: auto;
            max-height: 25;
            width: 100%;
            margin: 1 0;
            align: center middle;
        }}

        /* Clickable image container styling */
        ClickableImage {{
            border: solid transparent;
        }}

        ClickableImage:hover {{
            border: solid {cls.COLORS['foreground']};
            background: #2a2a5a;
        }}

        /* Remove borders from ListItems containing images */
        ListView ListItem.image-container {{
            border: none;
            padding: 0;
            margin: 0;
            background: {cls.COLORS['background']};
        }}

        /* Make URLs in TextAreas clickable hyperlinks */
        TextArea {{
            link-color: {cls.COLORS['blue']};
            link-background: transparent;
            link-style: underline;
        }}

        TextArea:hover {{
            link-color: {cls.COLORS['white']};
        }}
        """