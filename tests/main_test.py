# SPDX-FileCopyrightText: (c) 2021 Artëm IG <github.com/rtmigo>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import os
import sys
import textwrap
import unittest
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from timeit import default_timer as timer

from vien import main_entry_point
from vien.main import VenvExistsError, VenvDoesNotExistError, VienChildExit
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

    def test_run_needs_venv(self):
        with self.assertRaises(VenvDoesNotExistError):
            main_entry_point(["run", "python", "--version"])

    def test_run_exit_code_0(self):
        """Test that main_entry_point returns the same exit code,
        as the called command"""
        main_entry_point(["create"])  # need venv to run
        with self.assertRaises(VienChildExit) as ce:
            main_entry_point(["run", "python3", "-c", "exit(0)"])
        self.assertEqual(ce.exception.code, 0)

    def test_run_exit_code_1(self):
        """Test that main_entry_point returns the same exit code,
        as the called command"""
        main_entry_point(["create"])  # need venv to run
        with self.assertRaises(VienChildExit) as ce:
            main_entry_point(["run", "python3", "-c", "exit(1)"])
        self.assertEqual(ce.exception.code, 1)

    def test_run_exit_code_2(self):
        """Test that main_entry_point returns the same exit code,
        as the called command"""
        main_entry_point(["create"])  # need venv to run
        with self.assertRaises(VienChildExit) as ce:
            main_entry_point(["run", "python3", "-c", "exit(2)"])
        self.assertEqual(ce.exception.code, 2)

    def test_run(self):
        main_entry_point(["create"])

        with self.assertRaises(VienChildExit):
            # just check the argparser handles --version properly
            # (was failing with nargs='*', ok with nargs=argparse.REMAINDER)
            main_entry_point(["run", "python3", "--version"])

    def test_run_python_code(self):
        """Testing vien run python3 -c '...'"""
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

        lines = [line.strip() for line in python_program.splitlines()]
        python_program = "; ".join(line for line in lines if line)

        with self.assertRaises(SystemExit):
            main_entry_point(["run", "python3", "-c", python_program])

        # check the file created (it means, the command was executed)
        self.assertTrue(file_to_be_created.exists())

        # the file should contain the path or the python interpreter that
        # executed it in virtualenv
        interpreter_path = Path(file_to_be_created.read_text())

        self.assertTrue("svetdir" in interpreter_path.parts)
        self.assertTrue("project_venv" in interpreter_path.parts)

    def test_call_needs_venv(self):
        """File exists, but venv does not exist"""
        runme_py = self.projectDir / "runme.py"
        runme_py.touch()
        with self.assertRaises(VenvDoesNotExistError):
            main_entry_point(["call", str(runme_py)])

    def _call_for_exit_code(self, exit_code: int):
        (self.projectDir / "main.py").write_text(f"exit({exit_code})")
        main_entry_point(["create"])
        with self.assertRaises(SystemExit) as ce:
            main_entry_point(["call", "main.py"])
        self.assertEqual(ce.exception.code, exit_code)

    def test_call_42(self):
        """Calling a temporary .py script that must return 42.
        Testing whether it runs and whether we get correct exit code."""
        self._call_for_exit_code(42)

    def test_call_23(self):
        """Calling a temporary .py script that must return 23.
        Testing whether it runs and whether we get correct exit code."""
        self._call_for_exit_code(23)

    def test_call_parameters(self):
        """Testing that call really passes parameters to child."""

        main_entry_point(["create"])
        (self.projectDir / "main.py").write_text(
            f"import sys; exit(len(sys.argv))")

        with self.assertRaises(VienChildExit) as ce:
            main_entry_point(["call", "main.py"])
        self.assertEqual(ce.exception.code, 1)  # received len(argv)

        with self.assertRaises(VienChildExit) as ce:
            main_entry_point(["call", "main.py", "aaa", "bbb", "ccc"])
        self.assertEqual(ce.exception.code, 4)  # received len(argv)

    def test_call_project_dir(self):
        main_entry_point(["create"])
        pkg_dir = self.projectDir / "subpkg"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").touch()
        run_py = (pkg_dir / "run.py")
        run_py.write_text("exit(5)")

        run_py_str = str(run_py.absolute())
        with TemporaryDirectory() as td:
            os.chdir(td)

            # without -p we assume that the current dir is the project dir,
            # but the current is temp. So we must get an exception
            with self.assertRaises(VenvDoesNotExistError):
                main_entry_point(["call", run_py_str])

            # this call specifies project dir relative to run.py.
            # It runs the file successfully
            with self.assertRaises(VienChildExit) as ce:
                main_entry_point(["call", "-p", "..", run_py_str])
            self.assertEqual(ce.exception.code, 5)

            # this call specifies project dir relative to run.py.
            # It runs the file successfully
            with self.assertRaises(VienChildExit) as ce:
                main_entry_point(["call", "--project-dir", "..", run_py_str])
            self.assertEqual(ce.exception.code, 5)

            # this call specifies *incorrect* project dir relative to run.py.
            with self.assertRaises(VenvDoesNotExistError):
                main_entry_point(["call", "--project-dir", "../..", run_py_str])

    def test_shell_ok(self):
        main_entry_point(["create"])

        with TemporaryDirectory() as td:
            dir_to_create = Path(td) / "to_be_or_not_to_be"
            self.assertFalse(dir_to_create.exists())
            dir_to_create_quoted = repr(str(dir_to_create))
            bash_input = f'mkdir {dir_to_create_quoted}\n'

            # I did not find an easy way to run an interactive sub-shell during
            # testing and then to kill it. Solutions that were based on
            # signal.SIGALRM or the subprocess.run(timeout), were harming the
            # MacOS terminal that started the test
            #
            # So we provide input and delay arguments to the sub-shell. It
            # makes the sub-shell peacefully close itself.
            #
            # It is not a clean test for "shell" though. The "shell" meant to
            # be run without parameters.

            start = timer()
            with TimeLimited(10):  # safety net
                with self.assertRaises(VienChildExit) as ce:
                    main_entry_point(
                        ["shell", "--input", bash_input, "--delay", "1"])
                self.assertFalse(ce.exception.code, 0)
            end = timer()

            self.assertGreater(end - start, 0.5)
            self.assertLess(end - start, 3)
            self.assertTrue(dir_to_create.exists())

    def test_shell_exit_code_non_zero(self):
        main_entry_point(["create"])
        with TimeLimited(10):  # safety net
            with self.assertRaises(VienChildExit) as ce:
                main_entry_point(["shell", "--input", "exit 42"])
            self.assertEqual(ce.exception.code, 42)

    def test_shell_exit_code_zero(self):
        main_entry_point(["create"])
        with TimeLimited(10):  # safety net
            with self.assertRaises(VienChildExit) as ce:
                main_entry_point(["shell", "--input", "exit"])
            self.assertFalse(ce.exception.code, 0)

    def test_shell_but_no_venv(self):
        # python3 -m unittest svet.main_test.TestsInsideTempProjectDir.test_shell

        with TimeLimited(10):  # safety net
            with self.assertRaises(VenvDoesNotExistError) as cm:
                main_entry_point(["shell"])
