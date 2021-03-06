#!/usr/bin/env python3

if __name__ == "__main__":
    import unittest, os
    parent_dir = os.path.dirname(__file__)
    tests = unittest.TestLoader().discover(
        top_level_dir=parent_dir,
        start_dir=os.path.join(parent_dir, "svet"),
        pattern="*.py")
    testRunner = unittest.runner.TextTestRunner(buffer=True)
    testRunner.run(tests)
