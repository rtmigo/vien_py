# SPDX-FileCopyrightText: (c) 2021 Artëm IG <github.com/rtmigo>
# SPDX-License-Identifier: BSD-3-Clause

import os
import unittest
from pathlib import Path

from tests.common import is_posix
from vien._main import get_vien_dir


@unittest.skipUnless(is_posix, "not POSIX")
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