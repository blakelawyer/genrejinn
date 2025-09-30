#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Server mode functionality for web browser access."""

import os
import sys
import argparse


def debug_log(message):
    """Debug logging function."""
    with open('data/log.txt', 'a') as f:
        f.write(f"{message}\n")
        f.flush()


class ServerManager:
    """Manage server mode operations and configuration."""

    def __init__(self):
        self.is_server_mode = os.environ.get('GENREJINN_SERVER_MODE') == '1'

    def is_running_in_server_mode(self) -> bool:
        """Check if the application is running in server mode."""
        return self.is_server_mode

    def setup_server_environment(self) -> None:
        """Setup environment variables for server mode."""
        os.environ['GENREJINN_SERVER_MODE'] = '1'

    def get_server_config(self) -> dict:
        """Get server configuration from environment or defaults."""
        return {
            'host': os.environ.get('GENREJINN_HOST', '127.0.0.1'),
            'port': int(os.environ.get('GENREJINN_PORT', 8000)),
            'public_url': os.environ.get('GENREJINN_PUBLIC_URL'),
            'debug': os.environ.get('GENREJINN_DEBUG', 'false').lower() == 'true'
        }

    def parse_server_arguments(self) -> argparse.Namespace:
        """Parse command line arguments for server mode."""
        parser = argparse.ArgumentParser(description='GenreJinn EPUB Reader')
        parser.add_argument('--server', action='store_true',
                          help='Run in server mode for web browser access')
        parser.add_argument('--host', default='127.0.0.1',
                          help='Host address for server mode (default: 127.0.0.1)')
        parser.add_argument('--port', type=int, default=8000,
                          help='Port for server mode (default: 8000)')
        parser.add_argument('--public-url',
                          help='Public URL for server mode (e.g., https://blakelawyer.dev/genrejinn)')
        return parser.parse_args()

    def run_server_mode(self, host: str, port: int, public_url: str = None) -> None:
        """Run the application in server mode using textual-serve."""
        try:
            from textual_serve.server import Server
        except ImportError:
            print("Error: textual-serve is not installed. Install it with: pip install textual-serve")
            return

        print(f"Starting GenreJinn server on {host}:{port}")
        if public_url:
            print(f"Public URL: {public_url}")

        # Set environment variable that the subprocess can detect
        self.setup_server_environment()

        # Create server with current script as command
        server = Server(
            command=f'python {sys.argv[0]}',
            host=host,
            port=port,
            public_url=public_url
        )
        server.serve()

    def should_enable_link_detection(self) -> bool:
        """Determine if link detection should be enabled (server mode)."""
        return self.is_server_mode

    def process_urls_for_display(self, text: str) -> str:
        """Process URLs in text based on server mode settings."""
        if self.is_server_mode:
            # In server mode, preserve URLs for clickable links
            return text
        else:
            # In local mode, URLs might be hidden by image processing
            return text

    def get_textual_serve_available(self) -> bool:
        """Check if textual-serve is available."""
        try:
            import textual_serve
            return True
        except ImportError:
            return False