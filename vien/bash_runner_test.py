# SPDX-FileCopyrightText: (c) 2021 Artëm IG <github.com/rtmigo>
# SPDX-License-Identifier: BSD-3-Clause


import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from timeit import default_timer as timer

from .bash_runner import *
from .time_limited import TimeLimited


class TestRunAsBash(unittest.TestCase):

    # python3 -m unittest svet.bash_runner_test

    def test_good_command_code_zero(self):
        bash_lines = [
            f'set -e',
            f"ls"]
        code = run_as_bash_script("\n".join(bash_lines))
        self.assertEqual(code.returncode, 0)  # ok

    def test_bad_command_error_code(self):
        bash_lines = [
            f'set -e',
            f"ok_computer_make_me_happy"]
        code = run_as_bash_script("\n".join(bash_lines))
        self.assertEqual(code.returncode, 127)  # error

    def test_alias_expansion(self):
        with TemporaryDirectory() as td:
            file_to_create = Path(td) / "to_be_or_not_to_be.txt"
            file_to_create_quoted = repr(str(file_to_create))
            bash_lines = [
                f'set -e',
                f"shopt -s expand_aliases",
                f'alias ohoho="echo"',  # this will work in bash, but not in sh
                f'ohoho "that is the answer" > {file_to_create_quoted}']
            self.assertFalse(file_to_create.exists())
            code = run_as_bash_script("\n".join(bash_lines))
            self.assertEqual(code.returncode, 0)
            self.assertTrue(file_to_create.exists())
            self.assertEqual(file_to_create.read_text().strip(), "that is the answer")

    def test_input_delay(self):
        start = timer()
        # run interactive shell end type "exit" after small delay
        with TimeLimited(seconds=10):  # safety net
            run_as_bash_script("exec bash", input="exit\n".encode(), input_delay=1, timeout=10)
        end = timer()
        self.assertGreater(end - start, 0.9)
        self.assertLess(end - start, 5)
