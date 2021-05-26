import os
import unittest

from vien.main import _insert_into_pythonpath


@unittest.skipUnless(os.name == 'posix', "posix colons format")
class PythonPathTestPosix(unittest.TestCase):
    def test_empty(self):
        os.environ["PYTHONPATH"] = ''
        self.assertEqual(_insert_into_pythonpath('/a/b/c'),
                         '/a/b/c')

    def test_empty_multiple(self):
        os.environ["PYTHONPATH"] = ':::'
        self.assertEqual(_insert_into_pythonpath('/a/b/c'),
                         '/a/b/c')

    def test_empties_skipped(self):
        os.environ["PYTHONPATH"] = ':xx:::::yy:::'
        self.assertEqual(_insert_into_pythonpath('/a/b/c'),
                         '/a/b/c:xx:yy')

    def test_duplicates_skipped(self):
        os.environ["PYTHONPATH"] = 'aaa:bbb:ccc'
        self.assertEqual(_insert_into_pythonpath('bbb'),
                         'aaa:bbb:ccc')

    def test_two(self):
        os.environ["PYTHONPATH"] = ' /bbb/ccc :  /dd/ee/ff '
        self.assertEqual(_insert_into_pythonpath('/a/b/c'),
                         '/a/b/c:/bbb/ccc:/dd/ee/ff')


@unittest.skipUnless(os.name == 'nt', "windows semicolons format")
class PythonPathTestWindows(unittest.TestCase):
    # most tests are done on POSIX. Here we just test ';' and 'C:/'
    def test_two(self):
        os.environ["PYTHONPATH"] = ' C:/ccc/33 ;  D:/ddd/44 '
        self.assertEqual(_insert_into_pythonpath('E:/my/project'),
                         'E:/my/project;C:/ccc/33;D:/ddd/44')


if __name__ == "__main__":
    unittest.main()