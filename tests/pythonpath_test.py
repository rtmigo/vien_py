import os
import unittest

from vien.main import _insert_into_pythonpath


@unittest.skipUnless(os.name == 'posix', "posix colons format")
class PythonPathTestPosix(unittest.TestCase):
    def test_empty(self):
        try:
            del os.environ["PYTHONPATH"]
        except KeyError:
            pass
        self.assertEqual(_insert_into_pythonpath('/a/b/c'),
                         '/a/b/c:')

    def test_empty_multiple(self):
        os.environ["PYTHONPATH"] = '/x/11:/y/22'
        self.assertEqual(_insert_into_pythonpath('/path/to/project'),
                         '/path/to/project:/x/11:/y/22')


@unittest.skipUnless(os.name == 'nt', "windows semicolons format")
class PythonPathTestWindows(unittest.TestCase):
    # most tests are done on POSIX. Here we just test ';' and 'C:/'
    def test_two(self):
        os.environ["PYTHONPATH"] = 'D:/x/11;D:/y/22'
        self.assertEqual(_insert_into_pythonpath('E:/path/to/project'),
                         'E:/path/to/project;D:/x/11;D:/y/22')


if __name__ == "__main__":
    unittest.main()
