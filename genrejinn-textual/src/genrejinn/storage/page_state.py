#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Page state persistence for current reading position."""

import pickle
import os
from pathlib import Path


def debug_log(message):
    """Debug logging function."""
    with open('data/log.txt', 'a') as f:
        f.write(f"{message}\n")
        f.flush()


class PageStateManager:
    """Manage current page state persistence."""

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or "data/current_page.pkl"
        self.storage_dir = Path(self.storage_path).parent
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_current_page(self, current_page: int) -> None:
        """Save the current page number to a file."""
        try:
            with open(self.storage_path, 'wb') as f:
                pickle.dump(current_page, f)
            debug_log(f"Saved current page: {current_page}")
        except Exception as e:
            debug_log(f"Error saving current page: {e}")

    def load_current_page(self, total_pages: int) -> int:
        """Get the saved page number from a file."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'rb') as f:
                    saved_page = pickle.load(f)
                # Ensure the saved page is within valid bounds
                if 0 <= saved_page < total_pages:
                    debug_log(f"Found saved page: {saved_page}")
                    return saved_page
                else:
                    debug_log(f"Saved page {saved_page} out of bounds, starting at page 0")
                    return 0
            else:
                debug_log("No current page file found, starting at page 0")
                return 0
        except Exception as e:
            debug_log(f"Error loading current page: {e}")
            return 0

    def get_storage_info(self) -> dict:
        """Get information about the page state file."""
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