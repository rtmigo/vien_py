# SPDX-FileCopyrightText: (c) 2021 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import os
import sys
import unittest
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from svet import runmain
from svet.main import VenvExistsError, VenvDoesNotExistError


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
			runmain()
		self.assertEqual(cp.exception.code, 2)

	def test_help(self):
		with self.assertRaises(SystemExit) as cp:
			runmain(["-h"])
		self.assertEqual(cp.exception.code, 0)

	def test_path(self):
		os.chdir(Path(__file__).parent)
		runmain(["path"])


# todo test run

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

		os.environ["SVETDIR"] = str(self.svetDir.absolute())

	def tearDown(self):
		self._td.cleanup()
		del os.environ["SVETDIR"]

	def assertVenvDoesNotExist(self):
		self.assertFalse(self.expectedVenvDir.exists())
		self.assertFalse(self.expectedVenvBin.exists())

	def assertVenvExists(self):
		self.assertTrue(self.expectedVenvDir.exists())
		self.assertTrue(self.expectedVenvBin.exists())

	def test_create_with_argument(self):
		self.assertFalse(self.expectedVenvDir.exists())
		self.assertFalse(self.expectedVenvBin.exists())

		runmain(["create", "python3"])

		self.assertTrue(self.expectedVenvDir.exists())
		self.assertTrue(self.expectedVenvBin.exists())

	def test_create_fails_if_twice(self):
		runmain(["create"])
		with self.assertRaises(VenvExistsError):
			runmain(["create"])

	def test_recreate_with_argument(self):
		self.assertFalse(self.expectedVenvDir.exists())
		self.assertFalse(self.expectedVenvBin.exists())

		runmain(["create", "python3"])

		self.assertTrue(self.expectedVenvDir.exists())
		self.assertTrue(self.expectedVenvBin.exists())

		os.remove(self.expectedVenvBin)

		self.assertFalse(self.expectedVenvBin.exists())

		runmain(["recreate", "python3"])
		self.assertTrue(self.expectedVenvBin.exists())

		runmain(["recreate", "python3"])
		self.assertTrue(self.expectedVenvBin.exists())

	def test_init_wo_argument(self):
		self.assertFalse(self.expectedVenvDir.exists())
		self.assertFalse(self.expectedVenvBin.exists())

		runmain(["create"])

		self.assertTrue(self.expectedVenvDir.exists())
		self.assertTrue(self.expectedVenvBin.exists())

	def test_reinit_wo_argument(self):
		self.assertFalse(self.expectedVenvDir.exists())
		self.assertFalse(self.expectedVenvBin.exists())

		runmain(["recreate"])

		self.assertTrue(self.expectedVenvDir.exists())
		self.assertTrue(self.expectedVenvBin.exists())

	def test_create_then_delete(self):
		self.assertVenvDoesNotExist()
		runmain(["create"])
		self.assertVenvExists()
		runmain(["delete"])
		self.assertVenvDoesNotExist()

	def test_delete_fails_if_not_exist(self):
		self.assertVenvDoesNotExist()
		with self.assertRaises(VenvDoesNotExistError):
			runmain(["delete"])

	def test_shell_fails_if_not_exist(self):
		self.assertVenvDoesNotExist()
		with self.assertRaises(VenvDoesNotExistError):
			runmain(["shell"])

	def test_run(self):
		runmain(["create"])

		with self.assertRaises(SystemExit):
			# just check the argparser handles --version properly
			# (was failing with nargs='*', ok with nargs=argparse.REMAINDER)
			runmain(["run", "python", "--version"])

	def test_run_create_dir(self):
		runmain(["create"])

		markerDir = self.projectDir / "stub"
		self.assertFalse(markerDir.exists())

		# we will run python interpreter to create unexisting directory

		runme = f"import os; os.mkdir({repr(str(markerDir))})"
		with self.assertRaises(SystemExit):
			runmain(["run", "python", "-c", runme])

		# check it created
		self.assertTrue(markerDir.exists())
