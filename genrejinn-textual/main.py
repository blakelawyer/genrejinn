#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Legacy entry point for backward compatibility."""

# This file provides backward compatibility for the old entry point
# while using the new modular structure

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from genrejinn.main import main

if __name__ == "__main__":
    main()