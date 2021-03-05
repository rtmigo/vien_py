# SPDX-FileCopyrightText: (c) 2020 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause


import argparse

from vep import __version__

venvsRoot = "~/.pyvnv/"

helptxt = f"""
# -- PYVNV --------------------------------------------------------------------

VEP helps managing virtual environments located in {venvsRoot} 

For a Python project /path/to/myProject/ virtualenv will be located in 
in {venvsRoot}myProject_venv/

To CREATE new virtualenv with Python 3.8 in {venvsRoot}myProject_venv/:

	cd /path/to/myProject
	pyvnv init 3.8
	
To REMOVE old and CREATE new virtualenv:

	cd /path/to/myProject
	pyvnv reinit 3.8
 		
To RUN a PYTHON SCRIPT inside "myProject_venv" environment:	

	cd /path/to/myProject
	pyvnv run python ./myProgram.py
	
To RUN a BASH SUBSHELL inside "myProject_venv" environment:	

	cd /path/to/myProject
	pyvnv shell

"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import *

verbose = False


def run(args: List[str]):
	if verbose:
		print(f"Running {args}")
	subprocess.run(args)


def runseq(commands: List[str]):
	joined = ' && '.join(commands)
	if verbose:
		print(f"Running '{joined}'")
	return os.system(joined)


def quote(arg: str) -> str:
	return json.dumps(arg)


def findPython(version: str):
	for path in [
		"/Library/Frameworks/Python.framework/Versions/VER/bin/python3",
		"/usr/local/opt/python@VER/bin/python3",
	]:
		path = path.replace("VER", version)
		if os.path.exists(path):
			return path
	raise FileNotFoundError(f"Cannot find Python version {version}")


def venvDirToExe(venvDir: Path) -> Path:
	return venvDir / "bin" / "python"


def init(venvDir: Path, version: str):
	if venvDir.exists():
		raise Exception("Venv already exists.")

	exe = findPython(version)

	print(f"Creating {venvDir}")
	args = [exe, "-m", "venv", str(venvDir)]
	run(args)
	print()
	print("Configure PyCharm with Python executable:")
	print(str(venvDirToExe(venvDir)))

def reinit(venvDir: Path, version: str):
	if not "venv" in str(venvDir.absolute()):
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
		ps = f"venv@{venvName}> "

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
	print(__version__)

def runmain():

	parser = argparse.ArgumentParser()
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

	venvsParentDir = Path(os.path.expanduser(venvsRoot)).absolute()
	projectDir = Path(".").absolute()
	venvDir = venvsParentDir / (projectDir.name + "_venv")

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





