# SPDX-FileCopyrightText: (c) 2021 Artëm IG <github.com/rtmigo>
# SPDX-License-Identifier: BSD-3-Clause

import os
import unittest

from vien._call_funcs import relative_fn_to_module_name, NotInnerPath, \
    relative_inner_path


def rip(a: str, b: str) -> str:
    if os.name == 'posix':
        a = a.replace("W:", "")
        b = b.replace("W:", "")
    return relative_inner_path(a, b)


class TestRelativeInnerPath(unittest.TestCase):

    def assertEqualAnyslash(self, a: str, b: str):
        self.assertEqual(a.replace('\\', '/'),
                         b.replace('\\', '/'))

    def test_child(self):
        self.assertEqualAnyslash(
            rip('W:/abc/myProject/file.py', 'W:/abc/myProject'),
            'file.py')

    def test_sub_child(self):
        self.assertEqualAnyslash(
            rip('W:/abc/myProject/pkg/sub/file.py',
                'W:/abc/myProject'),
            'pkg/sub/file.py')

    @unittest.skipUnless(os.name == 'nt', "windows-specific")
    def test_sub_child_back(self):
        self.assertEqualAnyslash(
            rip('W:\\abc\\myProject\\pkg\\sub\\file.py',
                'W:\\abc\\myProject'),
            'pkg/sub/file.py')

    def test_both_relative(self):
        self.assertEqualAnyslash(
            rip('myProject/pkg/sub/file.py',
                'myProject'),
            'pkg/sub/file.py')

    def test_same(self):
        with self.assertRaises(NotInnerPath):
            rip('W:/abc/myProject/x', 'W:/abc/myProject/x'),

    def test_swapped(self):
        with self.assertRaises(NotInnerPath):
            rip('W:/abc', 'W:/abc/myProject/x'),

    @unittest.skipUnless(os.name == 'nt', "windows-specific")
    def test_swapped_backslash(self):
        with self.assertRaises(NotInnerPath):
            rip('W:\\abc', 'W:\\abc\\myProject\\x'),

    def test_neighbor(self):
        with self.assertRaises(NotInnerPath):
            rip('W:/abc', 'W:/abc/myProject/x'),


class TestFnToModuleName(unittest.TestCase):

    def test_fwd(self):
        self.assertEqual(
            relative_fn_to_module_name('pkg/sub/module.py'),
            'pkg.sub.module')

    def test_py_uppercase(self):
        self.assertEqual(
            relative_fn_to_module_name('pkg/sub/module.PY'),
            'pkg.sub.module')

    def test_no_slashes(self):
        self.assertEqual(
            relative_fn_to_module_name('file.py'),
            'file')

    @unittest.skipUnless(os.name == 'nt', "windows-specific")
    def test_back(self):
        self.assertEqual(
            relative_fn_to_module_name('pkg\\sub\\module.py'),
            'pkg.sub.module')

    def test_no_py(self):
        with self.assertRaises(ValueError):
            relative_fn_to_module_name('pkg/sub/module')

    def test_dots_ext(self):
        with self.assertRaises(ValueError):
            relative_fn_to_module_name('pkg/sub/module.ext.py')

    def test_dots_parent(self):
        with self.assertRaises(ValueError):
            relative_fn_to_module_name('../sub/module.ext.py')

    def test_dots_name(self):
        with self.assertRaises(ValueError):
            relative_fn_to_module_name('sub/.module.py')


if __name__ == "__main__":
    unittest.main()
