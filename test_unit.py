#!/usr/bin/env python3

import unittest
from pathlib import Path


def suite():
    """Can be imported into `setup.py` as `test_suite="test_unit.suite"`."""

    parent_dir = Path(__file__).parent
    init_py, = parent_dir.glob("*/__init__.py")

    return unittest.TestLoader().discover(
        top_level_dir=str(parent_dir),
        start_dir=str(init_py.parent),
        pattern="*.py")


def run_tests():
    """Discovers and runs unit tests for the module."""

    result = unittest.TextTestRunner(buffer=True).run(suite())

    if result.failures or result.errors:
        exit(1)


if __name__ == "__main__":
    run_tests()
