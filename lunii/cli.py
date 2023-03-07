# cli for lumiios
# WIP-- TODO later

# Path: lumiios/cli.py

import argparse
import logging
import os
import sys
from pathlib import Path

from . import Device, Story, utils

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description="A Python package for working with Lunii devices, and emulating them",
        epilog="For more information, visit github.com/bastien8060/lumiios",
    )
    
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s 0.1.0a1",
    )

    args = parser.parse_args()

    if args.version:
        print("lumiios 0.1.0a1")
        sys.exit(0)

 