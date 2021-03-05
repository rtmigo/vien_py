# SPDX-FileCopyrightText: (c) 2020 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

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


if __name__ == "__main__":

	import sys

	command = sys.argv[1]

	venvsParentDir = Path(os.path.expanduser(venvsRoot)).absolute()

	projectDir = Path(".").absolute()
	venvDir = venvsParentDir / (projectDir.name + "_venv")

	venvName = projectDir.name
	if venvName.endswith("_py"):
		venvName = venvName[:-3]

	if verbose:
		print(f"Proj dir: {projectDir}")
		print(f"Venv dir: {venvDir}")

	if command == "path":
		print(venvDir)
		exit(0)

	if command == "reinit":

		if len(sys.argv) < 3:
			print("Usage: pyvnv reinit X.X")
			exit(1)
		version = sys.argv[2]

		if os.path.exists(venvDir):
			print(f"Removing {venvDir}")
			shutil.rmtree(str(venvDir))
		init(venvDir=venvDir, version=version)
		exit(0)

	if command == "init":

		if len(sys.argv) < 3:
			print("Usage: pyvnv init X.X")
			exit(1)
		version = sys.argv[2]

		init(venvDir=venvDir, version=version)

		exit(0)

	if command == "shell":
		useColor = False
		YELLOW = ""  # "\e[33m"
		CYAN = r"\e[36m"
		NOCOLOR = r"\e[0m"  #

		activatePathQuoted = quote(str(venvDir / "bin" / "activate"))



		commands = [
			f'source {activatePathQuoted}',
			f'export PS1="venv@{venvName}> "',
			# f'export PS1="\\[{CYAN}venv@{venvName}>{NOCOLOR} \\]"', # fancy but buggy
			'exec bash'
		]

		exit(runseq(commands))

	if command == "run":
		otherargs = sys.argv[2:]

		commands = [
			f'source "{venvDir}/bin/activate"',
			" ".join(quote(a) for a in otherargs)
		]

		exit(runseq(commands))

	print("Error: Unexpected argument(s)")
	exit(1)
