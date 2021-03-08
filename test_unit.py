#!/usr/bin/env python3

import unittest
from pathlib import Path


def run_tests():
    """Discovers and runs unit tests for the module."""

    parent_dir = Path(__file__).parent
    the_init_file, = parent_dir.glob("*/__init__.py")

    tests = unittest.TestLoader().discover(
        top_level_dir=str(parent_dir),
        start_dir=str(the_init_file.parent),
        pattern="*.py")

    result = unittest.TextTestRunner(buffer=True).run(tests)

    if result.failures or result.errors:
        exit(1)


if __name__ == "__main__":
    run_tests()
