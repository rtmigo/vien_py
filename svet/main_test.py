# SPDX-FileCopyrightText: (c) 2021 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from svet import runmain
from svet.main import VenvExistsError, VenvDoesNotExistError


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

	def assertVenvDoesNotExist(self):
		self.assertFalse(self.expectedVenvDir.exists())
		self.assertFalse(self.expectedVenvBin.exists())

	def assertVenvExists(self):
		self.assertTrue(self.expectedVenvDir.exists())
		self.assertTrue(self.expectedVenvBin.exists())

	def tearDown(self):
		self._td.cleanup()
		del os.environ["SVETDIR"]

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
