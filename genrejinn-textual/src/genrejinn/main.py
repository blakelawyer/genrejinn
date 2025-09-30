#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Main entry point for GenreJinn EPUB Reader."""

import sys
import os

# Add the current directory to Python path for backward compatibility
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from .app import EPUBReader
from .utils.server import ServerManager


def main():
    """Main entry point for the application."""
    server_manager = ServerManager()
    args = server_manager.parse_server_arguments()

    if args.server:
        # Run in server mode
        server_manager.run_server_mode(args.host, args.port, args.public_url)
    else:
        # Run locally
        app = EPUBReader()
        app.run()


if __name__ == "__main__":
    main()