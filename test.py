#!/usr/bin/env python3

import sys
import os
import unittest

if __name__ == "__main__":

    parent_dir = os.path.dirname(__file__)

    tests = unittest.TestLoader().discover(
        top_level_dir=parent_dir,
        start_dir=os.path.join(parent_dir, "svet"),
        pattern=sys.argv[1] if len(sys.argv) > 1 else "*.py")

    result = unittest.runner.TextTestRunner(buffer=True).run(tests)

    if result.failures or result.errors:
        exit(1)
