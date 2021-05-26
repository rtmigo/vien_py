import unittest
from pathlib import Path

from tests.common import is_posix
from vien.main import get_project_dir
from vien.arg_parser import Parsed, Commands


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


class TestParseCall(unittest.TestCase):

    def test_outdated_p(self):
        pd = Parsed('-p a/b/c call -p d/e/f myfile.py arg1 arg2'.split())
        self.assertEqual(pd.args_to_python, ['myfile.py', 'arg1', 'arg2'])

    def test_p(self):
        pd = Parsed('-p a/b/c call -d myfile.py a b c'.split())
        self.assertEqual(pd.args_to_python, ['-d', 'myfile.py', 'a', 'b', 'c'])

    def test_unrecoginzed(self):
        """Unrecognized arguments that are NOT after the 'call' word."""
        with self.assertRaises(SystemExit) as ce:
            Parsed('-labuda call myfile.py a b c'.split())
        self.assertEqual(ce.exception.code, 2)


class TestParseShell(unittest.TestCase):
    def test_no_args(self):
        pd = Parsed('shell'.split())
        self.assertEqual(pd.command, Commands.shell)
        self.assertEqual(pd.shell_delay, None)
        self.assertEqual(pd.shell_input, None)

    def test_input(self):
        pd = Parsed(['shell', '--input', 'cd / && ls'])
        self.assertEqual(pd.shell_input, 'cd / && ls')

    def test_delay(self):
        pd = Parsed('shell --delay 1.2'.split())
        self.assertEqual(pd.shell_delay, 1.2)

    def test_labuda(self):
        with self.assertRaises(SystemExit) as ce:
            pd = Parsed('shell --labuda'.split())
        self.assertEqual(ce.exception.code, 2)


class TestParseRun(unittest.TestCase):
    def test(self):
        pd = Parsed(['run', 'python3', '-OO', 'file.py'])
        self.assertEqual(pd.command, Commands.run)
        self.assertEqual(pd.run_args, ['python3', '-OO', 'file.py'])


class TestParseCreate(unittest.TestCase):
    def test_with_arg(self):
        pd = Parsed(['create', 'python3'])
        self.assertEqual(pd.command, Commands.create)
        self.assertEqual(pd.python_executable, "python3")

    def test_without_arg(self):
        pd = Parsed(['create'])
        self.assertEqual(pd.command, Commands.create)
        self.assertEqual(pd.python_executable, None)


class TestParseRecreate(unittest.TestCase):
    def test_with_arg(self):
        pd = Parsed(['recreate', 'python3'])
        self.assertEqual(pd.command, Commands.recreate)
        self.assertEqual(pd.python_executable, "python3")

    def test_without_arg(self):
        pd = Parsed(['recreate'])
        self.assertEqual(pd.command, Commands.recreate)
        self.assertEqual(pd.python_executable, None)


if __name__ == "__main__":
    unittest.main()
