#!/usr/bin/env python3

# This file should be the main entry point when running "campdown".

"""Campdown
Usage:
  campdown <url> <optional output folder>
"""

# TODO: Insert extra command line arguments.

import sys

# Uncommented this since I wasn't sure if that was causing errors. Still has
# issues either way.
#import campdown


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

    #downloader = Downloader(url, out)

    try:
        pass
        # downloader.run()

    except (KeyboardInterrupt):
        print("\nInterrupt caught. Exiting program...")
        sys.exit(2)

# Check that this file's main function is not being called from another file.
if __name__ == "__main__":
    main()
