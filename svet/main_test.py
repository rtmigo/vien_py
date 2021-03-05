# SPDX-FileCopyrightText: (c) 2021 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from svet import runmain


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

	def test_init(self):
		self.assertFalse(self.expectedVenvDir.exists())
		self.assertFalse(self.expectedVenvBin.exists())

		runmain(["init", "python3"])

		self.assertTrue(self.expectedVenvDir.exists())
		self.assertTrue(self.expectedVenvBin.exists())

	def test_reinit(self):
		self.assertFalse(self.expectedVenvDir.exists())
		self.assertFalse(self.expectedVenvBin.exists())

		runmain(["init", "python3"])

		self.assertTrue(self.expectedVenvDir.exists())
		self.assertTrue(self.expectedVenvBin.exists())

		os.remove(self.expectedVenvBin)

		self.assertFalse(self.expectedVenvBin.exists())

		runmain(["reinit", "python3"])
		self.assertTrue(self.expectedVenvBin.exists())

		runmain(["reinit", "python3"])
		self.assertTrue(self.expectedVenvBin.exists())