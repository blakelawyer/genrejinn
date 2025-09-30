#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Image download and management."""

import os
import re
import urllib.parse
import requests
from pathlib import Path


def debug_log(message):
    """Debug logging function."""
    with open('data/log.txt', 'a') as f:
        f.write(f"{message}\n")
        f.flush()


class ImageManager:
    """Manage image downloads and storage."""

    def __init__(self, images_dir: str = None):
        self.images_dir = Path(images_dir or "data/images")
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def download_image(self, url: str) -> str:
        """Download image from URL to images directory and return filepath."""
        try:
            # Get filename from URL
            parsed_url = urllib.parse.urlparse(url)
            filename = os.path.basename(parsed_url.path)

            # If no filename, generate one
            if not filename or '.' not in filename:
                filename = f"image_{hash(url) % 10000}.jpg"

            filepath = self.images_dir / filename

            # Check if already downloaded
            if filepath.exists():
                return str(filepath)

            # Download the image with proper headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # Save to file
            with open(filepath, 'wb') as f:
                f.write(response.content)

            debug_log(f"Downloaded image: {url} -> {filepath}")
            return str(filepath)

        except Exception as e:
            debug_log(f"Image download failed: {e}")
            return None

    def process_note_for_images(self, note_text: str) -> tuple:
        """Process note text to find and download image URLs, return (processed_text, image_data)."""
        if not note_text:
            return "", []

        # Pattern to find URLs ending in .jpg or .png
        image_pattern = r'https?://[^\s]+\.(?:jpg|png)(?:\?[^\s]*)?'

        image_urls = re.findall(image_pattern, note_text, re.IGNORECASE)
        image_data = []  # List of (url, filepath) tuples
        processed_text = note_text

        # Check if we're running in server mode (via environment variable)
        is_server_mode = os.environ.get('GENREJINN_SERVER_MODE') == '1'

        for url in image_urls:
            filepath = self.download_image(url)
            if filepath:
                image_data.append((url, filepath))

                # Hide URLs in both local and server mode now
                debug_log(f"Hiding URL {url}")
                processed_text = processed_text.replace(url, "")

        # Clean up extra whitespace after removing URLs
        processed_text = re.sub(r'\s+', ' ', processed_text).strip()

        return processed_text, image_data

    def parse_image_references(self, text: str) -> list:
        """Parse text for image URLs or references and return list of found images."""
        image_references = []

        # Regex patterns for different image reference formats
        patterns = [
            # URL patterns (http/https)
            r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp|svg)(?:\?[^\s]*)?',
            # Markdown image syntax ![alt](url)
            r'!\[[^\]]*\]\(([^\)]+\.(?:jpg|jpeg|png|gif|webp|svg)(?:\?[^\)]*)?)\)',
            # HTML image tags <img src="url">
            r'<img[^>]+src=["\']([^"\']+\.(?:jpg|jpeg|png|gif|webp|svg)(?:\?[^"\']*)?)["\'][^>]*>',
            # Simple file references (local files)
            r'[^\s]+\.(?:jpg|jpeg|png|gif|webp|svg)'
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if match.groups():
                    # Extract URL from capturing group (for markdown/html)
                    url = match.group(1)
                else:
                    # Use the full match (for direct URLs)
                    url = match.group(0)

                if url not in image_references:
                    image_references.append(url)
                    debug_log(f"Found image reference: {url}")

        return image_references

    def get_storage_info(self) -> dict:
        """Get information about the images directory."""
        if self.images_dir.exists():
            # Count files in the directory
            image_files = list(self.images_dir.glob("*"))
            total_size = sum(f.stat().st_size for f in image_files if f.is_file())
            return {
                'exists': True,
                'count': len(image_files),
                'total_size': total_size,
                'path': str(self.images_dir)
            }
        else:
            return {
                'exists': False,
                'count': 0,
                'total_size': 0,
                'path': str(self.images_dir)
            }

    def cleanup_unused_images(self, referenced_images: set) -> int:
        """Remove unused images from storage, return count of removed files."""
        if not self.images_dir.exists():
            return 0

        removed_count = 0
        for image_file in self.images_dir.glob("*"):
            if image_file.is_file() and str(image_file) not in referenced_images:
                try:
                    image_file.unlink()
                    removed_count += 1
                    debug_log(f"Removed unused image: {image_file}")
                except Exception as e:
                    debug_log(f"Error removing image {image_file}: {e}")

        return removed_count