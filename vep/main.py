# SPDX-FileCopyrightText: (c) 2020 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause


import datetime as dt
import argparse
from tempfile import TemporaryDirectory

from vep import __version__
from vep.bashAliasRunner import runWithBashAliases

venvsRoot = "~/.pyvnv/"

__doc__ = f"""
# 

VEP helps managing virtual environments located in {venvsRoot} 

For a Python project /path/to/myProject/ virtualenv will be located in 
in {venvsRoot}myProject_venv/

To CREATE new virtualenv with Python 3.8 in {venvsRoot}myProject_venv/:

	cd /path/to/myProject
	vep init 3.8
	
To REMOVE old and CREATE new virtualenv:

	cd /path/to/myProject
	vep reinit 3.8
 		
To RUN a PYTHON SCRIPT inside "myProject_venv" environment:	

	cd /path/to/myProject
	vep run python ./myProgram.py
	
To RUN a BASH SUBSHELL inside "myProject_venv" environment:	

	cd /path/to/myProject
	vep shell

"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import *

verbose = False

import unittest

def getVepsDir() -> Path:

	s = os.environ.get("VEPDIR")
	if s:
		return Path(os.path.expanduser(os.path.expandvars(s)))
	else:
		return Path(os.path.expandvars("$HOME"))/".vepvep"

class TestVenvsDir(unittest.TestCase):

	def test_if_set_plain(self):
		os.environ["VEPDIR"] = "/path/to/veps"
		self.assertEqual(getVepsDir(), Path('/path/to/veps'))

	def test_if_set_with_vars(self):
		os.environ["VEPDIR"] = "$HOME/subfolder"
		s = str(getVepsDir())
		self.assertTrue("$" not in s)
		self.assertGreater(len(s), len("/home/"))

	def test_if_set_with_user(self):
		os.environ["VEPDIR"] = "~/subfolder"
		s = str(getVepsDir())
		self.assertTrue("~" not in s)
		self.assertGreater(len(s), len("/home/"))

	def test_if_not_n(self):
		if "VEPDIR" in os.environ:
			del os.environ["VEPDIR"]
		p = str(getVepsDir())
		self.assertTrue(p.endswith("vepvep"))
		self.assertGreater(len(p), len("/.vepvep"))




def run(args: List[str]):
	if verbose:
		print(f"Running {args}")
	subprocess.run(args, shell=True)


def runseq(commands: List[str]):
	joined = ' && '.join(commands)
	if verbose:
		print(f"Running '{joined}'")
	return os.system(joined)


def quote(arg: str) -> str:
	return json.dumps(arg)


def venvDirToExe(venvDir: Path) -> Path:
	return venvDir / "bin" / "python"


def init(venvDir: Path, version: str):
	if venvDir.exists():
		raise Exception("Venv already exists.")

	exe = version

	print(f"Creating {venvDir}")

	runWithBashAliases(f'{exe} -m venv "{str(venvDir)}"')

	print()
	print("Configure PyCharm with Python executable:")
	print(str(venvDirToExe(venvDir)))

def reinit(venvDir: Path, version: str):
	if not "_venv" in venvDir.name:
		raise Exception
	if venvDir.exists():
		print(f"Removing {venvDir}")
		shutil.rmtree(str(venvDir))
	init(venvDir=venvDir, version=version)

def shell(venvDir: Path, venvName:str):

	useColor = False
	YELLOW = ""  # "\e[33m"
	CYAN = r"\e[36m"
	NOCOLOR = r"\e[0m"  #

	activatePathQuoted = quote(str(venvDir / "bin" / "activate"))

	if useColor:
		ps = f"\\[{CYAN}venv@{venvName}>{NOCOLOR} \\]" # fancy but buggy
	else:
		ps = f"vep@{venvName}"

	commands = [
		f'source {activatePathQuoted}',
		f'export PS1="{ps}> "',
		'exec bash'
	]

	exit(runseq(commands))

def runargs(venvDir: Path, otherargs):
		commands = [
			f'source "{venvDir}/bin/activate"',
			" ".join(quote(a) for a in otherargs)
		]

		exit(runseq(commands))

def ver():
	m = max(p.stat().st_mtime for p in Path(__file__).parent.glob("*"))
	y = dt.datetime.fromtimestamp(m).year
	print(f"VEP {__version__} : (c) 2020-{y} Art Galkin <ortemeo@gmail.com>")
	print(f"https://github.com/rtmigo/vep#readme")

def runmain():

	parser = argparse.ArgumentParser(description="See https://github.com/rtmigo/vep#readme for details.")
	subparsers = parser.add_subparsers(dest='command', required=True)

	parser_init = subparsers.add_parser('init', help="Create new virtualenv")
	parser_init.add_argument('python', type=str)

	parser_reinit = subparsers.add_parser('reinit', help="Remove existing virtualenv and create new")
	parser_reinit.add_argument('python', type=str)

	subparsers.add_parser('shell', help="Dive into Bash subshell using the virtualenv")

	parser_run =subparsers.add_parser('run', help="Run a command inside the virtualenv")
	parser_run.add_argument('otherargs', nargs='*')

	subparsers.add_parser('path', help="Show the supposed path of the virtualenv for the current directory")
	subparsers.add_parser('ver', help="Print program version")

	args = parser.parse_args()

	###########

	#venvsParentDir = Path(os.path.expanduser(venvsRoot)).absolute()
	projectDir = Path(".").absolute()
	venvDir = getVepsDir()/(projectDir.name + "_venv") #venvsParentDir / (projectDir.name + "_venv")

	if verbose:
		print(f"Proj dir: {projectDir}")
		print(f"Venv dir: {venvDir}")

	##########

	if args.command == "init":
		init(venvDir, args.python)
	elif args.command == "reinit":
		reinit(venvDir, args.python)
	elif args.command == "path":
		print(venvDir)
	elif args.command == "run":
		runargs(venvDir, args.otherargs)
	elif args.command == "shell":
		shell(venvDir, projectDir.name)
	elif args.command == "ver":
		ver()
	else:
		raise ValueError





