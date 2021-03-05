# SPDX-FileCopyrightText: (c) 2021 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import os
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import *


def iterExistingProfileFiles() -> Iterator[str]:
	for possibleProfileFile in [
		"~/.bash_profile",
		"~/.bashrc",
		"~/.profile"]:
		possibleProfileFile = os.path.expanduser(possibleProfileFile)
		if os.path.exists(possibleProfileFile):
			yield possibleProfileFile


# todo make separate package from it?

def runWithBashAliases(commands: Union[str, List[str]]):
	# AG 2021-03: this the only way I found on MacOS 10.13 to run
	# a command with aliases defined in ~/.bash_profile.
	#
	# did not work:
	# 	subprocess.run(command_with_alias, shell=True)
	# 	subprocess.call(command_with_alias, shell=True)
	#	os.system(command_with_alias)
	# and longer ways like
	#	https://stackoverflow.com/a/25099813
	#	subprocess.call('command', shell=True, executable='/bin/bash')
	#	subprocess.call(['/bin/bash', '-i', '-c', command])
	# and their variations
	#
	# WORKING SOLUTION
	# ----------------
	# Create a temp .sh file like
	#
	#		#!/bin/bash
	#		shopt -s expand_aliases
	#		source ~/.bash_profile
	#		... command
	#
	# And
	#		scriptFile.chmod(0o775)
	#		subprocess.run(str(scriptFile))
	#
	# BETTER SOLUTION
	# ---------------
	# subprocess.call(file_content_as_string, shell=True)
	#
	# Also tried:
	#	"#!/usr/bin/env bash" instead of "#!/bin/bash"

	if isinstance(commands, str):
		commands = [commands]

	bashLines = [
		"#!/bin/bash"
		"set -e",  # fail on first error
		"shopt -s expand_aliases",  # turn on expansion
	]

	# the bash session still have no idea where to take the aliases.
	# We need to run "source"

	for possibleProfileFile in iterExistingProfileFiles():
		bashLines.append(f'source {possibleProfileFile}')

	bashLines.extend(commands)

	subprocess.call("\n".join(bashLines), shell=True)


class TestRunWithAliases(unittest.TestCase):

	def test_commands_support_aliases(self):
		with TemporaryDirectory() as td:
			temp = Path(td)
			child = temp / "child"
			self.assertFalse(child.exists())
			runWithBashAliases([
				'alias creatus_folderius="mkdir"',
				f'creatus_folderius {child}'])
			self.assertTrue(child.exists())

	def test_profile_file_found(self):
		self.assertTrue(any(iterExistingProfileFiles()))