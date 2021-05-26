import os
import unittest

from vien import is_posix
from vien._common import is_windows
from vien.main import _insert_into_pythonpath


@unittest.skipUnless(is_posix, "posix format")
class PythonPathTestPosix(unittest.TestCase):
    def test_empty(self):
        os.environ["PYTHONPATH"] = ''
        self.assertEqual(_insert_into_pythonpath('/a/b/c'),
                         '/a/b/c')

    def test_empty_multiple(self):
        os.environ["PYTHONPATH"] = ':::'
        self.assertEqual(_insert_into_pythonpath('/a/b/c'),
                         '/a/b/c')


    def test_two(self):
        os.environ["PYTHONPATH"] = ' /bbb/ccc :  /dd/ee/ff '
        self.assertEqual(_insert_into_pythonpath('/a/b/c'),
                         '/a/b/c:/bbb/ccc:/dd/ee/ff')


@unittest.skipUnless(is_windows, "windows format")
class PythonPathTestWindows(unittest.TestCase):
    def test_two(self):
        os.environ["PYTHONPATH"] = ' C:/bbb/ccc ;  D:/dd/ee/ff '
        self.assertEqual(_insert_into_pythonpath('E:/a/b/c'),
                         'C:/a/b/c;D:/bbb/ccc;E:/dd/ee/ff')


if __name__ == "__main__":
    unittest.main()
