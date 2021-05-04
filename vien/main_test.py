# SPDX-FileCopyrightText: (c) 2021 Artëm IG <github.com/rtmigo>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import os
import sys
import unittest
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from timeit import default_timer as timer

from vien import main_entry_point
from vien.main import VenvExistsError, VenvDoesNotExistError
from vien.time_limited import TimeLimited


class CapturedOutput:
    # ? maybe replace with https://pypi.org/project/stream-redirect/
    def __init__(self):
        self._new_out = StringIO()
        self._new_err = StringIO()

    def __enter__(self) -> CapturedOutput:
        self._old_stdout = sys.stdout
        self._old_stderr = sys.stderr
        sys.stdout = self._new_out
        sys.stderr = self._new_err
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._old_stdout
        sys.stderr = self._old_stderr

    @property
    def std(self) -> str:
        return self._new_out.getvalue()

    @property
    def err(self) -> str:
        return self._new_err.getvalue()


class Test(unittest.TestCase):
    def test_no_args(self):
        with self.assertRaises(SystemExit) as cp:
            main_entry_point()
        self.assertEqual(cp.exception.code, 2)

    def test_help(self):
        with self.assertRaises(SystemExit) as cp:
            main_entry_point(["-h"])
        self.assertEqual(cp.exception.code, 0)

    def test_path(self):
        os.chdir(Path(__file__).parent)
        main_entry_point(["path"])


class TestsInsideTempProjectDir(unittest.TestCase):

    def setUp(self):
        self._td = TemporaryDirectory()
        self.svetDir = Path(self._td.name) / "svetdir"
        self.projectDir = Path(self._td.name) / "project"

        self.projectDir.mkdir()
        self.svetDir.mkdir()

        os.chdir(self.projectDir)

        self.expectedVenvDir = self.svetDir / "project_venv"
        self.expectedVenvBin = self.expectedVenvDir / "bin" / "python"

        os.environ["VENVDIR"] = str(self.svetDir.absolute())

    def tearDown(self):
        self._td.cleanup()
        del os.environ["VENVDIR"]

    def assertVenvDoesNotExist(self):
        self.assertFalse(self.expectedVenvDir.exists())
        self.assertFalse(self.expectedVenvBin.exists())

    def assertVenvExists(self):
        self.assertTrue(self.expectedVenvDir.exists())
        self.assertTrue(self.expectedVenvBin.exists())

    def test_create_with_argument(self):
        self.assertFalse(self.expectedVenvDir.exists())
        self.assertFalse(self.expectedVenvBin.exists())

        main_entry_point(["create", "python3"])

        self.assertTrue(self.expectedVenvDir.exists())
        self.assertTrue(self.expectedVenvBin.exists())

    def test_create_fails_if_twice(self):
        main_entry_point(["create"])
        with self.assertRaises(VenvExistsError):
            main_entry_point(["create"])

    def test_recreate_with_argument(self):
        self.assertFalse(self.expectedVenvDir.exists())
        self.assertFalse(self.expectedVenvBin.exists())

        main_entry_point(["create", "python3"])

        self.assertTrue(self.expectedVenvDir.exists())
        self.assertTrue(self.expectedVenvBin.exists())

        os.remove(self.expectedVenvBin)

        self.assertFalse(self.expectedVenvBin.exists())

        main_entry_point(["recreate", "python3"])
        self.assertTrue(self.expectedVenvBin.exists())

        main_entry_point(["recreate", "python3"])
        self.assertTrue(self.expectedVenvBin.exists())

    def test_init_wo_argument(self):
        self.assertFalse(self.expectedVenvDir.exists())
        self.assertFalse(self.expectedVenvBin.exists())

        main_entry_point(["create"])

        self.assertTrue(self.expectedVenvDir.exists())
        self.assertTrue(self.expectedVenvBin.exists())

    def test_reinit_wo_argument(self):
        self.assertFalse(self.expectedVenvDir.exists())
        self.assertFalse(self.expectedVenvBin.exists())

        main_entry_point(["recreate"])

        self.assertTrue(self.expectedVenvDir.exists())
        self.assertTrue(self.expectedVenvBin.exists())

    def test_create_then_delete(self):
        self.assertVenvDoesNotExist()
        main_entry_point(["create"])
        self.assertVenvExists()
        main_entry_point(["delete"])
        self.assertVenvDoesNotExist()

    def test_delete_fails_if_not_exist(self):
        self.assertVenvDoesNotExist()
        with self.assertRaises(VenvDoesNotExistError) as cm:
            main_entry_point(["delete"])

    def test_shell_fails_if_not_exist(self):
        self.assertVenvDoesNotExist()
        with self.assertRaises(VenvDoesNotExistError) as cm:
            main_entry_point(["shell"])


    def test_run(self):
        main_entry_point(["create"])

        with self.assertRaises(SystemExit):
            # just check the argparser handles --version properly
            # (was failing with nargs='*', ok with nargs=argparse.REMAINDER)
            main_entry_point(["run", "python3", "--version"])

    def test_run_python(self):
        main_entry_point(["create"])

        file_to_be_created = self.projectDir / "hello.txt"
        self.assertFalse(file_to_be_created.exists())

        # we'll ask the python residing inside the virtualenv to create a text
        # file and write the path to interpreter in it

        python_program = f"""
            import os, sys
            from pathlib import Path
            Path({repr(str(file_to_be_created))}).write_text(sys.executable)
        """

        lines = [l.strip() for l in python_program.splitlines()]
        python_program = "; ".join(l for l in lines if l)

        with self.assertRaises(SystemExit):
            main_entry_point(["run", "python3", "-c", python_program])

        # check the file created (it means, the command was executed)
        self.assertTrue(file_to_be_created.exists())

        # the file should contain the path or the python interpreter that executed
        # it in virtualenv
        interpreter_path = Path(file_to_be_created.read_text())

        self.assertTrue("svetdir" in interpreter_path.parts)
        self.assertTrue("project_venv" in interpreter_path.parts)

    def test_shell_ok(self):
        main_entry_point(["create"])

        with TemporaryDirectory() as td:
            dir_to_create = Path(td) / "to_be_or_not_to_be"
            self.assertFalse(dir_to_create.exists())
            dir_to_create_quoted = repr(str(dir_to_create))
            bash_input = f'mkdir {dir_to_create_quoted}\n'

            # we did not find an easy way to run an interactive sub-shell during testing
            # and then to kill it. Solutions that were based on signal.SIGALRM or the
            # subprocess.run(timeout), were harming the MacOS terminal that started the test
            #
            # So we provide input and delay arguments to the sub-shell. It makes the
            # sub-shell peacefully close itself.
            #
            # It is not a clean test for "shell" though. The "shell" meant to be run
            # without parameters.

            start = timer()
            with TimeLimited(10):  # safety net
                main_entry_point(["shell", "--input", bash_input, "--delay", "1"])
            end = timer()

            self.assertGreater(end - start, 0.5)
            self.assertLess(end - start, 3)
            self.assertTrue(dir_to_create.exists())

    def test_shell_but_no_venv(self):
        # python3 -m unittest svet.main_test.TestsInsideTempProjectDir.test_shell

        with TimeLimited(10):  # safety net
            with self.assertRaises(VenvDoesNotExistError) as cm:
                main_entry_point(["shell"])

