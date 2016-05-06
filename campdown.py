#!/usr/bin/env python3

# Alternative to running setup.py and then using the main campdown command.

import campdown

# Check that this file's main function is not being called from another file.
if __name__ == "__main__":
    campdown.cli()
