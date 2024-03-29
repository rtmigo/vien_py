# SPDX-FileCopyrightText: (c) 2021 Artëm IG <github.com/rtmigo>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from timeit import default_timer as timer
from typing import List, Optional

from tests.common import is_posix
from tests.test_arg_parser import windows_too
from tests.time_limited import TimeLimited
from vien import main_entry_point
from vien._common import is_windows
from vien._exceptions import ChildExit, VenvExistsExit, VenvDoesNotExistExit, \
    PyFileNotFoundExit, CannotFindExecutableExit


class CapturedOutput:
    """Captures output of python functions (not a child process output,
    but own output)."""

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


class TempCwd:
    """Context manager that creates temp directory and makes it the current
    working directory until exit."""

    def __init__(self):
        self.prev_cwd: Optional[str] = None
        self.temp_dir: Optional[str] = None

    def __enter__(self):
        self.prev_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)
        return self.temp_dir

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.prev_cwd)
        shutil.rmtree(self.temp_dir)


EXPECTED_CREATE_LINES_COUNT = 10


class TestsInsideTempProjectDir(unittest.TestCase):

    def setUp(self):

        self._old_cwd = Path.cwd()

        self._temp_dir = tempfile.mkdtemp()

        self.svetDir = Path(self._temp_dir) / "svetdir"
        self.projectDir = Path(self._temp_dir) / "project"

        self.projectDir.mkdir()
        self.svetDir.mkdir()

        # creating two empty packages: pkg and pkg.sub
        self.project_pkg = self.projectDir / "pkg"
        self.project_pkg_sub = self.project_pkg / "sub"
        self.project_pkg_sub.mkdir(parents=True)
        (self.project_pkg_sub / "__init__.py").touch()
        (self.project_pkg / "__init__.py").touch()

        self.json_report_file: Optional[Path] = None

        os.chdir(self.projectDir)

        self.expectedVenvDir = self.svetDir / "project_venv"
        self.expectedVenvBinPosix = self.expectedVenvDir / "bin" / "python"
        self.expectedVenvBinWindows = self.expectedVenvDir / "Scripts" / "python.exe"

        os.environ["VIENDIR"] = str(self.svetDir.absolute())

    def tearDown(self):
        # moving out of project dir to stop "using" the _temp_dir
        os.chdir(self._old_cwd)
        # VIENDIR was assigned in setUp
        del os.environ["VIENDIR"]

        try:
            shutil.rmtree(self._temp_dir)
        except PermissionError as e:
            # PermissionError: [WinError 32] The process cannot access
            # the file because it is being used by another process:
            # C:\\Users\\RUNNER~1\\AppData\\Local\\Temp\\tmpzl8g6j0u\\project
            assert "WinError" in str(e)
            # It seems the reason for this exception was the CWD in _temp_dir.
            # But anyway I'll try to ignore it if it's possible

    def assertInVenv(self, inner: Path):
        inner_str = str(inner.absolute())
        outer_str = str(self.expectedVenvDir.absolute())

        # macOS weirdness
        inner_str = inner_str.replace("/private/var", "/var")
        outer_str = outer_str.replace("/private/var", "/var")

        if (os.path.commonpath([outer_str]) != os.path.commonpath(
                [outer_str, inner_str])):
            self.fail(f"Path '{inner_str}' is not inside the "
                      f"venv dir '{outer_str}'")

    def assertVenvBinExists(self):
        self.assertTrue(
            self.expectedVenvBinPosix.exists() or self.expectedVenvBinWindows.exists())

    def assertVenvBinNotExists(self):
        self.assertFalse(
            self.expectedVenvBinPosix.exists() or self.expectedVenvBinWindows.exists())

    def assertProjectDirIsNotCwd(self):
        basename = "marker"
        in_cwd = Path.cwd() / basename
        in_project = self.projectDir / basename

        self.assertFalse(in_cwd.exists())
        self.assertFalse(in_project.exists())

        in_cwd.touch()

        self.assertTrue(in_cwd.exists())
        self.assertFalse(in_project.exists())

    def assertVenvNotExists(self):
        self.assertFalse(self.expectedVenvDir.exists())
        self.assertVenvBinNotExists()

    def assertVenvExists(self):
        self.assertTrue(self.expectedVenvDir.exists())
        self.assertVenvBinExists()

    def assertIsErrorExit(self, exc: SystemExit):
        self.assertIsInstance(exc, SystemExit)
        self.assertTrue(exc.code is not None and exc.code != 0)

    def assertIsSuccessExit(self, exc: SystemExit):
        self.assertIsInstance(exc, SystemExit)
        self.assertTrue(exc.code is None or exc.code == 0)

    def write_reporting_program(self, py_file_path: Path) -> Path:
        self.json_report_file = py_file_path.parent / 'output.json'
        out_file_path_str = repr(str(self.json_report_file))
        code = "import pathlib, sys, json\n" \
               "d={'sys.path': sys.path, \n" \
               "   'sys.executable': sys.executable, \n" \
               "   'sys.argv': sys.argv\n" \
               "}\n" \
               "js=json.dumps(d)\n" \
               f"file=pathlib.Path({out_file_path_str})\n" \
               'file.write_text(js, encoding="utf-8")'
        py_file_path.write_text(code, encoding='utf-8')

        assert not self.json_report_file.exists()
        return self.json_report_file

    @property
    def report_exists(self) -> bool:
        return self.json_report_file is not None and \
               self.json_report_file.exists()

    @property
    def reported_syspath(self) -> List[str]:
        assert self.json_report_file is not None
        d = json.loads(self.json_report_file.read_text(encoding="utf-8"))
        return d["sys.path"]

    @property
    def reported_executable(self) -> Path:
        assert self.json_report_file is not None
        d = json.loads(self.json_report_file.read_text(encoding="utf-8"))
        return Path(d["sys.executable"])

    @property
    def reported_argv(self) -> List[str]:
        assert self.json_report_file is not None
        d = json.loads(self.json_report_file.read_text(encoding="utf-8"))
        return d["sys.argv"]

    ############################################################################

    def test_create_with_argument(self):
        # actually this is not a good test: we are not testing whether
        # argument is really used and not ignored
        self.assertVenvNotExists()
        self._run_and_check(["create", sys.executable], expected_exit_code=None,
                            expected_stdout_lines=EXPECTED_CREATE_LINES_COUNT)
        self.assertVenvExists()

    def test_create_fails_with_unresolvable_argument(self):
        # actually this is not a good test: we are not testing whether
        # argument is really used and not ignored
        self.assertVenvNotExists()
        with self.assertRaises(CannotFindExecutableExit) as ce:
            main_entry_point(["create", "labuda-ladeda-hehe"])
        self.assertIsErrorExit(ce.exception)
        self.assertVenvNotExists()

    def test_create_without_argument(self):
        self.assertVenvNotExists()
        main_entry_point(["create"])
        self.assertVenvExists()

    def test_create_fails_if_twice(self):
        main_entry_point(["create"])
        with self.assertRaises(VenvExistsExit) as ce:
            main_entry_point(["create"])
        self.assertIsErrorExit(ce.exception)

    @unittest.skipUnless(is_posix, "not sure what to resolve in windows")
    def test_create_resolves_python3(self):
        self.assertVenvNotExists()
        main_entry_point(["create", "python3"])
        self.assertVenvExists()

    ############################################################################

    def test_create_then_delete(self):
        self.assertVenvNotExists()
        main_entry_point(["create"])
        self.assertVenvExists()
        main_entry_point(["delete"])
        self.assertVenvNotExists()

    def test_delete_fails_if_not_exists(self):
        self.assertVenvNotExists()
        with self.assertRaises(VenvDoesNotExistExit) as cm:
            main_entry_point(["delete"])
        self.assertIsErrorExit(cm.exception)

    ############################################################################

    def test_recreate_without_argument(self):
        self.assertVenvNotExists()
        main_entry_point(["recreate"])
        self.assertVenvExists()

    def test_recreate_with_argument(self):
        self.assertVenvNotExists()

        main_entry_point(["create", sys.executable])

        self.assertTrue(self.expectedVenvDir.exists())

        if self.expectedVenvBinWindows.exists():
            os.remove(self.expectedVenvBinWindows)
        elif self.expectedVenvBinPosix.exists():
            os.remove(self.expectedVenvBinPosix)
        else:
            raise AssertionError("executable not found")

        self.assertVenvBinNotExists()

        main_entry_point(["recreate", sys.executable])
        self.assertVenvBinExists()

        main_entry_point(["recreate", sys.executable])
        self.assertVenvBinExists()

    def test_recreate_fails_with_unresolvable_argument(self):
        # actually this is not a good test: we are not testing whether
        # argument is really used and not ignored
        self.assertVenvNotExists()
        with self.assertRaises(CannotFindExecutableExit) as ce:
            main_entry_point(["recreate", "labuda-ladeda-hehe"])
        self.assertIsErrorExit(ce.exception)
        self.assertVenvNotExists()

    @unittest.skipUnless(is_posix, "not sure what to resolve in windows")
    def test_recreate_resolves_python3(self):
        self.assertVenvNotExists()
        main_entry_point(["recreate", "python3"])
        self.assertVenvExists()

    ############################################################################

    @unittest.skipUnless(is_windows, "testing windows limitations")
    def test_run_missing_in_windows(self):
        with self.assertRaises(SystemExit) as cm:
            main_entry_point(["run", "python", "-c", "pass"])
        self.assertEqual(cm.exception.code, 2)

    @unittest.skipUnless(is_posix, "not POSIX")
    def test_run_needs_venv(self):
        with self.assertRaises(VenvDoesNotExistExit) as cm:
            main_entry_point(windows_too(["run", "python", "-c", "pass"]))
        self.assertIsErrorExit(cm.exception)

    @unittest.skipUnless(is_posix, "not POSIX")
    def test_run_exit_code_0(self):
        """Test that main_entry_point returns the same exit code,
        as the called command"""
        main_entry_point(["create"])  # need venv to run
        with self.assertRaises(ChildExit) as ce:
            main_entry_point(windows_too(["run", "python3", "-c", "exit(0)"]))
        self.assertEqual(ce.exception.code, 0)

    @unittest.skipUnless(is_posix, "not POSIX")
    def test_run_exit_code_1(self):
        """Test that main_entry_point returns the same exit code,
        as the called command"""
        main_entry_point(["create"])  # need venv to run
        with self.assertRaises(ChildExit) as ce:
            main_entry_point(windows_too(["run", "python3", "-c", "exit(1)"]))
        self.assertEqual(ce.exception.code, 1)

    @unittest.skipUnless(is_posix, "not POSIX")
    def test_run_exit_code_2(self):
        """Test that main_entry_point returns the same exit code,
        as the called command"""
        main_entry_point(["create"])  # need venv to run
        with self.assertRaises(ChildExit) as ce:
            main_entry_point(windows_too(["run", "python3", "-c", "exit(2)"]))
        self.assertEqual(ce.exception.code, 2)

    @unittest.skipUnless(is_posix, "not POSIX")
    def test_run_python_version(self):
        main_entry_point(["create"])

        with self.assertRaises(ChildExit):
            # just check the argparser handles --version properly
            # (was failing with nargs='*', ok with nargs=argparse.REMAINDER)
            main_entry_point(windows_too(["run", "python3", "--version"]))

    def assertLinesCount(self, txt: str, count: int, string_name=''):
        real_count = len(txt.splitlines())
        if real_count != count:
            if string_name:
                string_name += ' '
            self.fail(f"The {string_name}string contains {real_count} lines "
                      f"(not {count}):\n"
                      "=====\n"
                      f"{txt}"
                      "\n====="
                      )

    def _run_and_get_stdout(self, args: List[str]) -> str:
        with TimeLimited(10):  # if the child does not stop, fail own process
            with CapturedOutput() as out:
                main_entry_point(args)
                return out.std

    def _run_and_check(self,
                       args: List[str],
                       expected_exit_code: Optional[int] = 0,
                       expected_stdout_lines: Optional[int] = 0,
                       expected_stderr_lines: Optional[int] = 0):
        with TimeLimited(10):  # if the child does not stop, fail own process
            with CapturedOutput() as out:
                if expected_exit_code is not None:
                    with self.assertRaises(ChildExit) as ce:
                        main_entry_point(args)
                    self.assertEqual(ce.exception.code, expected_exit_code)
                else:
                    main_entry_point(args)  # no exceptions expected

        if expected_stdout_lines is not None:
            self.assertLinesCount(out.std, expected_stdout_lines, "stdout")

        if expected_stderr_lines is not None:
            self.assertLinesCount(out.err, expected_stderr_lines, "stderr")

    @unittest.skipUnless(is_posix, "not POSIX")
    def test_run_p(self):
        """Checking the -p changes both venv directory and the first item
        in PYTHONPATH"""
        main_entry_point(["create"])
        with TemporaryDirectory() as temp_cwd:
            # we will run it NOT from the project dir as CWD
            os.chdir(temp_cwd)

            # creating .py file to run
            code_py = Path(temp_cwd) / "code.py"
            self.write_reporting_program(code_py)

            # running the code that will create a json file
            self.assertProjectDirIsNotCwd()
            self._run_and_check(
                ["-p", str(self.projectDir.absolute()),
                 "run", "python3", str(code_py)])

            self.assertInVenv(self.reported_executable)
            self.assertIn(str(self.projectDir.absolute()),
                          self.reported_syspath)

    @unittest.skipUnless(is_posix, "not POSIX")
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

        with self.assertRaises(SystemExit) as ce:
            main_entry_point(["run", "python3", "-c", python_program])
        self.assertIsSuccessExit(ce.exception)

        # check the file created (it means, the command was executed)
        self.assertTrue(file_to_be_created.exists())

        # the file should contain the path or the python interpreter that
        # executed it in virtualenv
        interpreter_path = Path(file_to_be_created.read_text())

        self.assertTrue("svetdir" in interpreter_path.parts)
        self.assertTrue("project_venv" in interpreter_path.parts)

    ## CALL ####################################################################

    def test_call_needs_venv(self):
        """File exists, but venv does not exist"""
        runme_py = self.projectDir / "runme.py"
        runme_py.touch()
        with self.assertRaises(VenvDoesNotExistExit) as ce:
            main_entry_point(["call", str(runme_py)])
        self.assertIsErrorExit(ce.exception)

    def test_call_nonexistent_file(self):
        main_entry_point(["create"])
        with self.assertRaises(PyFileNotFoundExit) as ce:
            main_entry_point(["call", "nonexistent.py"])
        self.assertIsErrorExit(ce.exception)

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

    def test_call_file_as_module(self):
        main_entry_point(["create"])

        # creating pkg/sub/module.py
        file_py = self.project_pkg_sub / "module.py"
        self.write_reporting_program(file_py)

        self.assertFalse(self.report_exists)

        # running from random CWD
        with TempCwd():
            self.assertProjectDirIsNotCwd()
            self._run_and_check(
                ["-p", str(self.projectDir.absolute()),
                 "call", "-m", str(file_py.absolute())])

        self.assertTrue(self.report_exists)
        self.assertInVenv(self.reported_executable)
        self.assertIn(str(self.projectDir.absolute()),
                      self.reported_syspath)

    def test_call_file_as_file(self):
        main_entry_point(["create"])

        # creating pkg/sub/module.py
        file_py = self.project_pkg_sub / "module.py"
        self.write_reporting_program(file_py)

        self.assertFalse(self.report_exists)

        # running from random CWD
        with TempCwd():
            self.assertProjectDirIsNotCwd()
            self._run_and_check(
                ["-p", str(self.projectDir.absolute()),
                 "call", str(file_py.absolute())])  # no -m

        self.assertTrue(self.report_exists)
        self.assertInVenv(self.reported_executable)
        self.assertIn(str(self.projectDir.absolute()),
                      self.reported_syspath)

    def test_call_parameters(self):
        """Testing that call really passes parameters to child."""

        main_entry_point(["create"])

        self.write_reporting_program(self.projectDir / "file.py")

        self.assertFalse(self.report_exists)
        self._run_and_check(["call", "file.py", "hello", "program"])
        self.assertTrue(self.report_exists)

        self.assertEqual(self.reported_argv[-2], "hello")
        self.assertEqual(self.reported_argv[-1], "program")

    def test_call_project_dir_venv(self):
        """Tests that the -p parameter actually changes the project directory,
        so the correct virtual environment is found."""

        main_entry_point(["create"])
        pkg_dir = self.projectDir / "subpkg"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").touch()
        run_py = (pkg_dir / "run.py")
        run_py.write_text("exit(5)")

        run_py_str = str(run_py.absolute())
        with TempCwd():
            # NORMAL format

            # this call specifies project dir relative to run.py.
            # It runs the file successfully
            with self.assertRaises(ChildExit) as ce:
                main_entry_point(["-p", "..", "call", run_py_str])
            self.assertEqual(ce.exception.code, 5)

            # this call specifies project dir relative to run.py.
            # It runs the file successfully
            with self.assertRaises(ChildExit) as ce:
                main_entry_point(
                    ["--project-dir", "..", "call", run_py_str])
            self.assertEqual(ce.exception.code, 5)

            # OUTDATED format

            # this call specifies project dir relative to run.py.
            # It runs the file successfully
            with self.assertRaises(ChildExit) as ce:
                main_entry_point(["call", "-p", "..", run_py_str])
            self.assertEqual(ce.exception.code, 5)

            # this call specifies project dir relative to run.py.
            # It runs the file successfully
            with self.assertRaises(ChildExit) as ce:
                main_entry_point(
                    ["call", "--project-dir", "..", run_py_str])
            self.assertEqual(ce.exception.code, 5)

            # ERRORS

            # without -p we assume that the current dir is the project dir,
            # but the current is temp. So we must get an exception
            with self.assertRaises(VenvDoesNotExistExit):
                main_entry_point(["call", run_py_str])

            # this call specifies INCORRECT project dir relative to run.py
            with self.assertRaises(VenvDoesNotExistExit):
                main_entry_point(
                    ["call", "--project-dir", "../..", run_py_str])
            # finally:
            #     os.chdir(self._old_cwd)  # to safely delete the temp dir

    def test_call_project_dir_relative_imports(self):
        """ Tests that modules are importable from the project dir
        set by -p parameter"""

        main_entry_point(["create"])
        pkg_dir = self.projectDir / "subpkg"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").touch()
        (pkg_dir / "constant.py").write_text("FIFTY_FIVE=55")
        run_py = (pkg_dir / "run.py")
        # thanks to modified PYTHONPATH, the following must work
        run_py.write_text("import subpkg.constant\n"
                          "exit(subpkg.constant.FIFTY_FIVE)")

        run_py_str = str(run_py.absolute())
        with TempCwd():
            self.assertProjectDirIsNotCwd()
            with self.assertRaises(ChildExit) as ce:
                main_entry_point(["-p", "..", "call", run_py_str])
            self.assertEqual(ce.exception.code, 55)

    ############################################################################

    @unittest.skipUnless(is_windows, "testing windows limitations")
    def test_shell_missing_in_windows(self):
        with self.assertRaises(SystemExit) as cm:
            main_entry_point(["run", "shell"])
        self.assertEqual(cm.exception.code, 2)

    @unittest.skipUnless(is_posix, "not POSIX")
    def test_shell_p(self):
        """Checking the -p changes both venv directory and the first item
        in PYTHONPATH"""
        main_entry_point(["create"])
        with TempCwd() as temp_cwd:
            # creating .py file to run
            code_py = Path(temp_cwd) / "code.py"
            output_file = self.write_reporting_program(code_py)

            # running the code that will create a json file
            self.assertProjectDirIsNotCwd()
            with self.assertRaises(ChildExit) as ce:
                main_entry_point(
                    ["-p", str(self.projectDir.absolute()),
                     "shell", "--input",
                     f'python3 "{code_py}"'])
            self.assertEqual(ce.exception.code, 0)

            # loading json and checking the values
            d = json.loads(output_file.read_text())
            self.assertIn(str(self.projectDir.absolute()), d["sys.path"])
            self.assertInVenv(Path(d["sys.executable"]))

    @unittest.skipUnless(is_posix, "not POSIX")
    def test_shell_fails_if_not_exist(self):
        self.assertVenvNotExists()
        with self.assertRaises(VenvDoesNotExistExit) as cm:
            main_entry_point(["shell"])
        self.assertIsErrorExit(cm.exception)

    @unittest.skipUnless(is_posix, "not POSIX")
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
            self._run_and_check(
                ["shell", "--input", bash_input, "--delay", "1"])
            end = timer()

            self.assertGreater(end - start, 0.5)
            self.assertLess(end - start, 5)
            self.assertTrue(dir_to_create.exists())

    @unittest.skipUnless(is_posix, "features implemented only for POSIX yet")
    def test_shell_exit_code_non_zero(self):
        main_entry_point(["create"])
        self._run_and_check(["shell", "--input", "exit 42"],
                            expected_exit_code=42)

    @unittest.skipUnless(is_posix, "not POSIX")
    def test_shell_exit_code_zero(self):
        main_entry_point(["create"])
        with TimeLimited(10):  # safety net
            self._run_and_check(["shell", "--input", "exit"],
                                expected_exit_code=0)

    @unittest.skipUnless(is_posix, "not POSIX")
    def test_shell_but_no_venv(self):
        with self.assertRaises(VenvDoesNotExistExit) as cm:
            main_entry_point(["shell"])
        self.assertIsErrorExit(cm.exception)

    # python3 -m unittest tests.test_main.TestsInsideTempProjectDir.test_shell_uses_modified_path

    @unittest.skipUnless(is_posix, "not POSIX")
    def test_shell_uses_modified_path(self):
        with TemporaryDirectory() as tds:
            file_with_path = Path(tds) / "path.txt"

            main_entry_point(["create"])
            try:
                main_entry_point(
                    ["-p", str(self.projectDir.absolute()),
                     "shell",
                     "--delay", "1",
                     "--input", f'echo $PATH > {file_with_path}'])
            except ChildExit:
                pass

            path = file_with_path.read_text()
            self.assertTrue(path.startswith(str(self.expectedVenvDir)),
                            path)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(TestsInsideTempProjectDir("test_create_with_argument"))
    unittest.TextTestRunner().run(suite)
