#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Highlight persistence and storage management."""

import pickle
import os
from pathlib import Path
from ..highlighting.colors import parse_highlight_tuple


def debug_log(message):
    """Debug logging function."""
    with open('data/log.txt', 'a') as f:
        f.write(f"{message}\n")
        f.flush()


class HighlightStorage:
    """Manage saving and loading of highlights."""

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or "data/highlights.pkl"
        self.storage_dir = Path(self.storage_path).parent
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_highlights(self, highlights: dict) -> None:
        """Save highlights to a pickle file."""
        try:
            with open(self.storage_path, 'wb') as f:
                pickle.dump(highlights, f)
            debug_log(f"Saved {len(highlights)} pages of highlights")
        except Exception as e:
            debug_log(f"Error saving highlights: {e}")

    def load_highlights(self) -> dict:
        """Load highlights from a pickle file."""
        highlights = {}
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'rb') as f:
                    highlights = pickle.load(f)
                debug_log(f"Loaded {len(highlights)} pages of highlights")

                # Convert old format highlights to new format with default yellow color
                highlights = self._convert_old_format(highlights)
                debug_log("Converted old highlight format to new format with colors")
            else:
                debug_log("No highlights file found, starting fresh")
        except Exception as e:
            debug_log(f"Error loading highlights: {e}")

        return highlights

    def _convert_old_format(self, highlights: dict) -> dict:
        """Convert old 4-element highlight format to new 5-element format."""
        for page_num, page_highlights in highlights.items():
            updated_highlights = []
            for highlight in page_highlights:
                if len(highlight) == 4:
                    # Old format: (start_pos, end_pos, text, note)
                    start_pos, end_pos, text, note = highlight
                    # Add yellow as default color, ensure text has yellow brackets
                    if not (text.startswith('[') and text.endswith(']')):
                        # Add yellow brackets if they're missing
                        clean_text = text.strip('[]{}()<>«»⟨⟩|')
                        text = f"[{clean_text}]"
                    updated_highlights.append((start_pos, end_pos, text, note, "yellow"))
                else:
                    # New format: keep as-is
                    updated_highlights.append(highlight)
            highlights[page_num] = updated_highlights

        return highlights

    def backup_highlights(self, highlights: dict, backup_name: str = None) -> None:
        """Create a backup of current highlights."""
        if backup_name is None:
            import time
            backup_name = f"highlights_backup_{int(time.time())}.pkl"

        backup_path = self.storage_dir / "backups" / backup_name
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(backup_path, 'wb') as f:
                pickle.dump(highlights, f)
            debug_log(f"Created highlight backup: {backup_path}")
        except Exception as e:
            debug_log(f"Error creating highlight backup: {e}")

    def get_storage_info(self) -> dict:
        """Get information about the storage file."""
        if os.path.exists(self.storage_path):
            size = os.path.getsize(self.storage_path)
            mtime = os.path.getmtime(self.storage_path)
            return {
                'exists': True,
                'size': size,
                'modified': mtime,
                'path': self.storage_path
            }
        else:
            return {
                'exists': False,
                'size': 0,
                'modified': None,
                'path': self.storage_path
            }