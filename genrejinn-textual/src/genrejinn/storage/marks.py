#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Mark persistence and storage management."""

import pickle
import os
import time
from pathlib import Path


def debug_log(message):
    """Debug logging function."""
    with open('data/log.txt', 'a') as f:
        f.write(f"{message}\n")
        f.flush()


class MarkStorage:
    """Manage saving and loading of marks."""

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or "data/marks.pkl"
        self.storage_dir = Path(self.storage_path).parent
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_marks(self, marks: list) -> None:
        """Save marks to a pickle file."""
        try:
            with open(self.storage_path, 'wb') as f:
                pickle.dump(marks, f)
            debug_log(f"Saved {len(marks)} marks")
        except Exception as e:
            debug_log(f"Error saving marks: {e}")

    def load_marks(self) -> list:
        """Load marks from a pickle file."""
        marks = []
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'rb') as f:
                    marks = pickle.load(f)
                debug_log(f"Loaded {len(marks)} marks")
            else:
                debug_log("No marks file found, starting fresh")
        except Exception as e:
            debug_log(f"Error loading marks: {e}")

        return marks

    def create_mark(self, page_num: int, start_row: int, start_col: int,
                   selected_text: str, mark_name: str) -> tuple:
        """Create a new mark tuple with timestamp."""
        timestamp = time.time()
        return (page_num, start_row, start_col, selected_text, mark_name, timestamp)

    def get_mark_key(self, mark: tuple) -> str:
        """Generate a unique key for a mark to track dropdown state."""
        if len(mark) >= 6:
            page_num, start_row, start_col, selected_text, mark_name, timestamp = mark[:6]
            return f"mark_{page_num}_{start_row}_{start_col}_{timestamp}"
        else:
            # Fallback for incomplete marks
            return f"mark_{mark[0]}_{mark[1]}_{mark[2]}_0"

    def sanitize_mark_id(self, mark_name: str) -> str:
        """Sanitize mark name for use as HTML/CSS ID."""
        mark_name_str = str(mark_name)
        sanitized_id = ''.join(c if c.isalnum() or c in '-_' else '-' for c in mark_name_str.lower())
        # Remove consecutive hyphens and strip leading/trailing hyphens
        sanitized_id = '-'.join(filter(None, sanitized_id.split('-')))
        return sanitized_id

    def backup_marks(self, marks: list, backup_name: str = None) -> None:
        """Create a backup of current marks."""
        if backup_name is None:
            backup_name = f"marks_backup_{int(time.time())}.pkl"

        backup_path = self.storage_dir / "backups" / backup_name
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(backup_path, 'wb') as f:
                pickle.dump(marks, f)
            debug_log(f"Created mark backup: {backup_path}")
        except Exception as e:
            debug_log(f"Error creating mark backup: {e}")

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