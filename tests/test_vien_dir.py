import os
import unittest
from pathlib import Path

from vien.main import get_vien_dir


class TestVenvsDir(unittest.TestCase):

    def test_if_set_plain(self):
        os.environ["VIENDIR"] = "/path/to/veps"
        self.assertEqual(get_vien_dir(), Path('/path/to/veps'))

    def test_if_set_with_vars(self):
        os.environ["VIENDIR"] = "$HOME/subfolder"
        s = str(get_vien_dir())
        self.assertTrue("$" not in s)
        self.assertGreater(len(s), len("/home/"))

    def test_if_set_with_user(self):
        os.environ["VIENDIR"] = "~/subfolder"
        s = str(get_vien_dir())
        self.assertTrue("~" not in s)
        self.assertGreater(len(s), len("/home/"))

    def test_if_not_n(self):
        if "VIENDIR" in os.environ:
            del os.environ["VIENDIR"]
        p = str(get_vien_dir())
        self.assertTrue(p.endswith("vien"))
        self.assertGreater(len(p), len("/.vien"))