# SPDX-FileCopyrightText: (c) 2020 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from typing import *

verbose = False

from svet import __version__


class SvetError(Exception):
	def __init__(self, message: str):
		super().__init__(message)


class VenvExistsError(SvetError): pass


class VenvDoesNotExistError(SvetError):
	def __init__(self):
		super().__init__("Virtualenv does not exist")


class CannotFindExecutableError(SvetError):
	pass


def version() -> str:
	modTimestamp = (Path(__file__).parent / "constants.py").stat().st_mtime
	modYear = dt.datetime.fromtimestamp(modTimestamp).year
	return "\n".join([
		f"SVET: Simple Virtual Environments Tool {__version__}",
		f"(c) 2020-{modYear} Art Galkin <ortemeo@gmail.com>",
		f"See https://github.com/rtmigo/svet#readme"
	])


def usageDoc():
	text = f"""{version()}

SVETDIR
-------

SVET maps project directory names to virtualenv paths.

  /here/myProject       -> $SVETDIR/myProject_venv
  /there/myProject      -> $SVETDIR/myProject_venv
  /there/otherProject   -> $SVETDIR/otherProject_venv

By default $SVETDIR is "~/.svet". You can redefine in with

  export SVETDIR="/other/location"

RUNNING
-------

CREATE new virtualenv with python3 in $SVETDIR/myProject_venv:

  cd /abc/myProject
  svet create python3

RUN an interactive BASH SUBSHELL inside "myProject_venv":	

  cd /abc/myProject
  svet shell
		
RUN a PYTHON SCRIPT inside "myProject_venv":	

  cd /abc/myProject
  svet run python ./myProgram.py arg1 arg2 ...

See HELP with other options:	

  svet -h

"""

	doc = text.strip()
	aboveFirstLine = ("-" * len(doc.splitlines()[0]))
	return f"{aboveFirstLine}\n{doc}\n"


def getSvetDir() -> Path:
	s = os.environ.get("SVETDIR")
	if s:
		return Path(os.path.expanduser(os.path.expandvars(s)))
	else:
		return Path(os.path.expandvars("$HOME")) / ".svet"


class TestVenvsDir(unittest.TestCase):

	def test_if_set_plain(self):
		os.environ["SVETDIR"] = "/path/to/veps"
		self.assertEqual(getSvetDir(), Path('/path/to/veps'))

	def test_if_set_with_vars(self):
		os.environ["SVETDIR"] = "$HOME/subfolder"
		s = str(getSvetDir())
		self.assertTrue("$" not in s)
		self.assertGreater(len(s), len("/home/"))

	def test_if_set_with_user(self):
		os.environ["SVETDIR"] = "~/subfolder"
		s = str(getSvetDir())
		self.assertTrue("~" not in s)
		self.assertGreater(len(s), len("/home/"))

	def test_if_not_n(self):
		if "SVETDIR" in os.environ:
			del os.environ["SVETDIR"]
		p = str(getSvetDir())
		self.assertTrue(p.endswith("svet"))
		self.assertGreater(len(p), len("/.svet"))


def run(args: List[str]):
	if verbose:
		print(f"Running {args}")
	subprocess.run(args, shell=True)


def runseq(commands: List[str]):
	bashLines = [
		"#!/bin/bash"
		"set -e",  # fail on first error
	]

	bashLines.extend(commands)

	subprocess.call("\n".join(bashLines), shell=True)


def quote(arg: str) -> str:
	return json.dumps(arg)


def venvDirToExe(venvDir: Path) -> Path:
	return venvDir / "bin" / "python"


def init(venvDir: Path, version: str):
	if venvDir.exists():
		raise VenvExistsError("Virtualenv already exists.")

	exe = shutil.which(version)
	if not exe:
		raise CannotFindExecutableError(f"Cannot resolve '{version}' to an executable file.")

	print(f"Creating {venvDir}")

	result = subprocess.run([exe, "-m", "venv", str(venvDir)])
	if result.returncode == 0:
		print()
		print("The Python executable:")
		print(str(venvDirToExe(venvDir)))
	else:
		print("svet failed to create the virtualenv")
		exit(1)


def remove(venvDir: Path):
	if not "_venv" in venvDir.name:
		raise ValueError(venvDir)
	if not venvDir.exists():
		raise VenvDoesNotExistError
	print(f"Removing {venvDir}")
	shutil.rmtree(str(venvDir))


def reinit(venvDir: Path, version: str):
	if venvDir.exists():
		remove(venvDir)
	init(venvDir=venvDir, version=version)


def shell(venvDir: Path, venvName: str):
	if not venvDir.exists():
		raise VenvDoesNotExistError

	useColor = True
	# YELLOW = "\e[33m"
	# CYAN = r"\e[36m"
	# NOCOLOR = r"\e[0m"  #

	GREEN = "\e[32m\]"
	MAGENDA = "\e[35m\]"
	YELLOW = "\e[33m\]"
	CYAN = r"\e[36m\]"
	BLUE = r"\e[34m\]"
	NOCOLOR = r"\e[0m\]"  #

	activatePathQuoted = quote(str(venvDir / "bin" / "activate"))

	venvName = "(" + venvName + ")"

	if useColor:
		ps = f"\\[{YELLOW}{venvName}{NOCOLOR}:{CYAN}\\W{NOCOLOR}$ \\]"  # fancy but buggy
	else:
		ps = f"vep@{venvName}$ "

	commands = [
		f'source {activatePathQuoted}',
		f'export PS1="{ps}"',
		'exec bash'
	]

	exit(runseq(commands))


def runargs(venvDir: Path, otherargs):
	vd = str(venvDir.absolute())
	commands = [
		f'source "{vd}/bin/activate"',
		" ".join(quote(a) for a in otherargs)
	]

	exit(runseq(commands))


def main_entry_point(args: Optional[List[str]] = None):
	# print(sys.argv)
	# exit()

	if args is None:
		args = sys.argv[1:]

	if not args:
		print(usageDoc())
		exit(2)

	# noinspection PyTypeChecker
	parser = argparse.ArgumentParser()

	subparsers = parser.add_subparsers(dest='command', required=True)

	parser_init = subparsers.add_parser('create', help="create new virtualenv")
	parser_init.add_argument('python', type=str, default="python3", nargs='?')

	subparsers.add_parser('delete', help="delete existing virtualenv")

	parser_reinit = subparsers.add_parser('recreate',
										  help="delete existing virtualenv and create new")
	parser_reinit.add_argument('python', type=str, default="python3", nargs='?')

	subparsers.add_parser('shell', help="dive into Bash subshell using the virtualenv")

	parser_run = subparsers.add_parser('run', help="run a command inside the virtualenv")
	parser_run.add_argument('otherargs', nargs=argparse.REMAINDER)  # nargs='*'

	subparsers.add_parser('path',
						  help="show the supposed path of the virtualenv for the current directory")

	args = parser.parse_args(args)

	###########

	projectDir = Path(".").absolute()
	venvDir = getSvetDir() / (
			projectDir.name + "_venv")  # venvsParentDir / (projectDir.name + "_venv")

	if verbose:
		print(f"Proj dir: {projectDir}")
		print(f"Venv dir: {venvDir}")

	##########

	if args.command == "create":
		init(venvDir, args.python)
	elif args.command == "recreate":
		reinit(venvDir, args.python)
	elif args.command == "delete":
		remove(venvDir)
	elif args.command == "path":
		print(venvDir)
	elif args.command == "run":
		runargs(venvDir, args.otherargs)
	elif args.command == "shell":
		shell(venvDir, projectDir.name)
	else:
		raise ValueError
