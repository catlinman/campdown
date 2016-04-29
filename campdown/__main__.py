#!/usr/bin/env python3

"""Campdown
Usage:
  campdown <url> <optional output folder>
"""

# TODO: Insert extra command line arguments.

import sys
from campdown.downloader import Downloader


def main():
    try:
        url = sys.argv[1]

    except(IndexError):
        print('\nMissing required URL argument')
        sys.exit(2)

    try:
        out = sys.argv[2]

    except(IndexError):
        out = ""

    downloader = Downloader(url, out)

    try:
        downloader.run()

    except (KeyboardInterrupt):
        print("\nInterrupt caught. Exiting program...")
        sys.exit(2)

# Check that this file's main function is not being called from another file.
if __name__ == "__main__":
    main()
