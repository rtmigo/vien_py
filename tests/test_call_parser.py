import unittest

from tests.common import is_posix
from vien.call_parser import items_after, call_pyfile, ParsedCall


class TestOld(unittest.TestCase):
    # remove?
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


class TestNew(unittest.TestCase):

    def test_file_after_call(self):
        psr = ParsedCall("vien -p zzz call -d FiLe.Py arg1".split())
        self.assertEqual(psr.file, "FiLe.Py")

    def test_file_before_and_after_call(self):
        psr = ParsedCall("vien -p wrong.py call -d right.py arg1".split())
        self.assertEqual(psr.file, "right.py")

    def test_file_not_found(self):
        with self.assertRaises(ValueError):
            ParsedCall("vien -p wrong.py call -d arg1".split())

    def test_before_exists(self):
        psr = ParsedCall("vien -p zzz call -m anyfile.py".split())
        self.assertEqual(psr.before_filename, "-m")

    def test_before_does_not_exist(self):
        psr = ParsedCall("vien -p zzz call anyfile.py".split())
        self.assertEqual(psr.before_filename, None)


if __name__ == "__main__":
    unittest.main()
