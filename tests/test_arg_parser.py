import unittest
from pathlib import Path

from vien.main import Parsed, get_project_dir


class TestProjectDir(unittest.TestCase):

    def test_run_short_left(self):
        pd = Parsed('-p a/b/c run python3 myfile.py'.split())
        self.assertEqual(pd.project_dir_arg, 'a/b/c')

    def test_run_long_left(self):
        pd = Parsed('--project-dir a/b/c run python3 myfile.py'.split())
        self.assertEqual(pd.project_dir_arg, 'a/b/c')

    def test_call_short_right(self):
        pd = Parsed('call -p a/b/c myfile.py'.split())
        self.assertEqual(pd.project_dir_arg, 'a/b/c')

    def test_call_long_right(self):
        pd = Parsed('call --project-dir a/b/c myfile.py'.split())
        self.assertEqual(pd.project_dir_arg, 'a/b/c')

    def test_call_short_left(self):
        pd = Parsed('-p a/b/c call myfile.py'.split())
        self.assertEqual(pd.project_dir_arg, 'a/b/c')

    def test_call_long_left(self):
        pd = Parsed('--project-dir a/b/c call myfile.py'.split())
        self.assertEqual(pd.project_dir_arg, 'a/b/c')

    def test_call_short_both(self):
        pd = Parsed('-p a/b/c call -p d/e/f myfile.py'.split())
        self.assertEqual(pd.project_dir_arg, 'd/e/f')


class TestCallOtherArgs(unittest.TestCase):

    def test_outdated_p(self):
        pd = Parsed('-p a/b/c call -p d/e/f myfile.py arg1 arg2'.split())
        self.assertEqual(pd.args_to_python, ['myfile.py', 'arg1', 'arg2'])

    def test_p(self):
        pd = Parsed('-p a/b/c call -d myfile.py a b c'.split())
        self.assertEqual(pd.args_to_python, ['-d', 'myfile.py', 'a', 'b', 'c'])



if __name__ == "__main__":
    unittest.main()
