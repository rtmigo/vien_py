# SPDX-FileCopyrightText: (c) 2021 Artëm IG <github.com/rtmigo>
# SPDX-License-Identifier: BSD-3-Clause

import unittest
from pathlib import Path
from typing import List

from vien._common import is_windows

from tests.common import is_posix
from vien._main import get_project_dir
from vien._parsed_args import ParsedArgs, Commands, _iter_after


def windows_too(args: List[str]) -> List[str]:
    """For the Windows platform, appends a secret parameter to the arguments
    so that Windows accepts even unsupported commands.

    This allows testing functionality that is only partially
    implemented for Windows.
    """
    if is_windows:
        return [ParsedArgs.PARAM_WINDOWS_ALL_ARGS] + args
    else:
        return args


class TestItemsAfter(unittest.TestCase):
    def test_items_after(self):
        self.assertEqual(list(_iter_after(['A', 'B', 'C'], 'A')),
                         ['B', 'C'])
        self.assertEqual(list(_iter_after(['A', 'B', 'C'], 'B')),
                         ['C'])
        self.assertEqual(list(_iter_after(['A', 'B', 'C'], 'C')),
                         [])
        with self.assertRaises(LookupError):
            list(_iter_after(['A', 'B', 'C'], 'X'))


class TestWindowsAllArgs(unittest.TestCase):
    @unittest.skipUnless(is_posix, "posix-only")
    def test_windowsallargs_fails_on_posix(self):
        # is the PARAM_WINDOWS_ALL_ARGS is set, we must run windows.
        # Otherwise, AssertionError is thrown
        with self.assertRaises(AssertionError):
            ParsedArgs([ParsedArgs.PARAM_WINDOWS_ALL_ARGS, 'shell'])


class TestProjectDir(unittest.TestCase):

    def test_run_short_left(self):
        pd = ParsedArgs(windows_too('-p a/b/c run python3 myfile.py'.split()))
        self.assertEqual(pd.project_dir_arg, 'a/b/c')

    def test_run_long_left(self):
        pd = ParsedArgs(
            windows_too('--project-dir a/b/c run python3 myfile.py'.split()))
        self.assertEqual(pd.project_dir_arg, 'a/b/c')

    def test_call_short_right(self):
        pd = ParsedArgs('call -p a/b/c myfile.py'.split())
        self.assertEqual(pd.project_dir_arg, 'a/b/c')

    def test_call_long_right(self):
        pd = ParsedArgs('call --project-dir a/b/c myfile.py'.split())
        self.assertEqual(pd.project_dir_arg, 'a/b/c')

    def test_call_short_left(self):
        pd = ParsedArgs('-p a/b/c call myfile.py'.split())
        self.assertEqual(pd.project_dir_arg, 'a/b/c')

    def test_call_long_left(self):
        pd = ParsedArgs('--project-dir a/b/c call myfile.py'.split())
        self.assertEqual(pd.project_dir_arg, 'a/b/c')

    def test_call_short_both(self):
        pd = ParsedArgs('-p a/b/c call -p d/e/f myfile.py'.split())
        self.assertEqual(pd.project_dir_arg, 'd/e/f')


class TestParseCall(unittest.TestCase):

    def test_outdated_p(self):
        pd = ParsedArgs('-p a/b/c call -p d/e/f myfile.py arg1 arg2'.split())
        self.assertEqual(pd.args_to_python, ['myfile.py', 'arg1', 'arg2'])

    def test_p(self):
        pd = ParsedArgs('-p a/b/c call -d myfile.py a b c'.split())
        self.assertEqual(pd.args_to_python, ['-d', 'myfile.py', 'a', 'b', 'c'])

    def test_unrecoginzed(self):
        """Unrecognized arguments that are NOT after the 'call' word."""
        with self.assertRaises(SystemExit) as ce:
            ParsedArgs('-labuda call myfile.py a b c'.split())
        self.assertEqual(ce.exception.code, 2)

    def test_call_field(self):
        pd = ParsedArgs('-p a/b/c call -m myfile.py arg1 arg2'.split())
        self.assertIsNotNone(pd.call)
        self.assertEqual(pd.call.filename, "myfile.py")
        self.assertEqual(pd.call.before_filename, "-m")


class TestParseShell(unittest.TestCase):
    def test_no_args(self):
        pd = ParsedArgs(windows_too('shell'.split()))
        self.assertEqual(pd.command, Commands.shell)
        self.assertEqual(pd.shell_delay, None)
        self.assertEqual(pd.shell_input, None)

    def test_input(self):
        pd = ParsedArgs(windows_too(['shell', '--input', 'cd / && ls']))
        self.assertEqual(pd.shell_input, 'cd / && ls')

    def test_delay(self):
        pd = ParsedArgs(windows_too('shell --delay 1.2'.split()))
        self.assertEqual(pd.shell_delay, 1.2)

    def test_labuda(self):
        with self.assertRaises(SystemExit) as ce:
            pd = ParsedArgs(windows_too('shell --labuda'.split()))
        self.assertEqual(ce.exception.code, 2)


class TestParseRun(unittest.TestCase):
    def test(self):
        pd = ParsedArgs(windows_too(['run', 'python3', '-OO', 'file.py']))
        self.assertEqual(pd.command, Commands.run)
        self.assertEqual(pd.run_args, ['python3', '-OO', 'file.py'])


class TestParseCreate(unittest.TestCase):
    def test_with_arg(self):
        pd = ParsedArgs(['create', 'python3'])
        self.assertEqual(pd.command, Commands.create)
        self.assertEqual(pd.python_executable, "python3")

    def test_without_arg(self):
        pd = ParsedArgs(['create'])
        self.assertEqual(pd.command, Commands.create)
        self.assertEqual(pd.python_executable, None)


class TestParseRecreate(unittest.TestCase):
    def test_with_arg(self):
        pd = ParsedArgs(['recreate', 'python3'])
        self.assertEqual(pd.command, Commands.recreate)
        self.assertEqual(pd.python_executable, "python3")

    def test_without_arg(self):
        pd = ParsedArgs(['recreate'])
        self.assertEqual(pd.command, Commands.recreate)
        self.assertEqual(pd.python_executable, None)


if __name__ == "__main__":
    unittest.main()
