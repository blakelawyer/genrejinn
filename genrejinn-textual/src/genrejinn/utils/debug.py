#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Debug logging utilities."""

import os
from pathlib import Path


class DebugLogger:
    """Centralized debug logging for GenreJinn."""

    def __init__(self, log_path: str = None):
        self.log_path = log_path or "data/log.txt"
        self.log_dir = Path(self.log_path).parent
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log(self, message: str) -> None:
        """Write a debug message to the log file."""
        try:
            with open(self.log_path, 'a') as f:
                f.write(f"{message}\n")
                f.flush()
        except Exception as e:
            # Fallback to print if logging fails
            print(f"Debug log error: {e}")
            print(f"Original message: {message}")

    def clear_log(self) -> None:
        """Clear the log file."""
        try:
            if os.path.exists(self.log_path):
                os.remove(self.log_path)
        except Exception as e:
            self.log(f"Error clearing log: {e}")

    def get_log_size(self) -> int:
        """Get the size of the log file in bytes."""
        try:
            if os.path.exists(self.log_path):
                return os.path.getsize(self.log_path)
            return 0
        except Exception:
            return 0

    def rotate_log(self, max_size_mb: int = 10) -> None:
        """Rotate log file if it exceeds max size."""
        max_size_bytes = max_size_mb * 1024 * 1024
        if self.get_log_size() > max_size_bytes:
            try:
                # Move current log to backup
                backup_path = f"{self.log_path}.backup"
                if os.path.exists(self.log_path):
                    os.rename(self.log_path, backup_path)
                self.log("Log rotated - previous log saved as backup")
            except Exception as e:
                self.log(f"Error rotating log: {e}")


# Global logger instance
_global_logger = DebugLogger()


def debug_log(message: str) -> None:
    """Global debug logging function for backward compatibility."""
    _global_logger.log(message)