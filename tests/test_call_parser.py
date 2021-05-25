import unittest

from tests.common import is_posix
from vien.call_parser import items_after, call_pyfile


class Test(unittest.TestCase):
    def test_items_after(self):
        self.assertEqual(list(items_after(['A', 'B', 'C'], 'A')),
                         ['B', 'C'])
        self.assertEqual(list(items_after(['A', 'B', 'C'], 'B')),
                         ['C'])
        self.assertEqual(list(items_after(['A', 'B', 'C'], 'C')),
                         [])
        with self.assertRaises(LookupError):
            list(items_after(['A', 'B', 'C'], 'X'))

    def test_call_pyfile(self):
        self.assertEqual(
            call_pyfile("vien -p zzz call -d file.py arg1".split()),
            "file.py")
        self.assertEqual(
            call_pyfile("vien -p zzz call -d arg1 arg2".split()),
            None)
        self.assertEqual(
            call_pyfile("vien -p zzz call -d File.PY arg1".split()),
            "File.PY")
        self.assertEqual(
            call_pyfile("vien aaa.py bbb.py call -d ccc.py arg1".split()),
            "ccc.py")


if __name__ == "__main__":
    unittest.main()
