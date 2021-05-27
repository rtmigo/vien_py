import os
import unittest

from vien.main import relative_inner_path, NotInnerPath


def rip(a: str, b: str) -> str:
    if os.name == 'posix':
        a = a.replace("W:", "")
        b = b.replace("W:", "")
    return relative_inner_path(a, b)


class TestRelativeInnerPath(unittest.TestCase):
    def test_child(self):
        self.assertEqual(
            rip('W:/abc/myProject/file.py', 'W:/abc/myProject'),
            'file.py')

    def test_sub_child(self):
        self.assertEqual(
            rip('W:/abc/myProject/pkg/sub/file.py',
                'W:/abc/myProject'),
            'pkg/sub/file.py')

    @unittest.skipUnless(os.name == 'posix', "windows-specific")
    def test_sub_child_back(self):
        self.assertEqual(
            rip(r'W:\abc\myProject\pkg\sub\file.py',
                r'W:\abc\myProject'),
            'pkg/sub/file.py')

    def test_both_relative(self):
        self.assertEqual(
            rip('myProject/pkg/sub/file.py',
                'myProject'),
            'pkg/sub/file.py')

    def test_same(self):
        with self.assertRaises(NotInnerPath):
            rip('W:/abc/myProject/x', 'W:/abc/myProject/x'),

    def test_swapped(self):
        with self.assertRaises(NotInnerPath):
            rip('W:/abc', 'W:/abc/myProject/x'),

    @unittest.skipUnless(os.name == 'posix', "windows-specific")
    def test_swapped_backslash(self):
        with self.assertRaises(NotInnerPath):
            rip(r'W:\abc', r'W:\abc\myProject\x'),

    def test_neighbor(self):
        with self.assertRaises(NotInnerPath):
            rip('W:/abc', 'W:/abc/myProject/x'),


if __name__ == "__main__":
    unittest.main()
