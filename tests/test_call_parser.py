import unittest

from vien.call_parser import ParsedCall

from vien.exceptions import PyFileArgNotFoundExit


class TestNew(unittest.TestCase):

    def test_file_after_call(self):
        psr = ParsedCall("vien -p zzz call -d FiLe.Py arg1".split())
        self.assertEqual(psr.file, "FiLe.Py")

    def test_file_before_and_after_call(self):
        psr = ParsedCall("vien -p wrong.py call -d right.py arg1".split())
        self.assertEqual(psr.file, "right.py")

    def test_file_not_found(self):
        with self.assertRaises(PyFileArgNotFoundExit):
            ParsedCall("vien -p wrong.py call -d arg1".split())

    def test_before_exists(self):
        psr = ParsedCall("vien -p zzz call -m anyfile.py".split())
        self.assertEqual(psr.before_filename, "-m")

    def test_before_does_not_exist(self):
        psr = ParsedCall("vien -p zzz call anyfile.py".split())
        self.assertEqual(psr.before_filename, None)


if __name__ == "__main__":
    unittest.main()
