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

from svet.bash_runner import run_as_bash_script

verbose = False

import svet


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
    mod_timestamp = (Path(__file__).parent / "constants.py").stat().st_mtime
    mod_year = dt.datetime.fromtimestamp(mod_timestamp).year
    return "\n".join([
        f"SVET: Simple Virtual Environments Tool {svet.__version__}",
        svet.__copyright__.replace("2020", f"2020-{mod_year}"),
        f"See https://github.com/rtmigo/svet#readme"
    ])


def usage_doc():
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

--------

"""

    doc = text.strip()
    above_first_line = ("-" * len(doc.splitlines()[0]))
    return f"{above_first_line}\n{doc}\n"


def get_svet_dir() -> Path:
    s = os.environ.get("SVETDIR")
    if s:
        return Path(os.path.expanduser(os.path.expandvars(s)))
    else:
        return Path(os.path.expandvars("$HOME")) / ".svet"


class TestVenvsDir(unittest.TestCase):

    def test_if_set_plain(self):
        os.environ["SVETDIR"] = "/path/to/veps"
        self.assertEqual(get_svet_dir(), Path('/path/to/veps'))

    def test_if_set_with_vars(self):
        os.environ["SVETDIR"] = "$HOME/subfolder"
        s = str(get_svet_dir())
        self.assertTrue("$" not in s)
        self.assertGreater(len(s), len("/home/"))

    def test_if_set_with_user(self):
        os.environ["SVETDIR"] = "~/subfolder"
        s = str(get_svet_dir())
        self.assertTrue("~" not in s)
        self.assertGreater(len(s), len("/home/"))

    def test_if_not_n(self):
        if "SVETDIR" in os.environ:
            del os.environ["SVETDIR"]
        p = str(get_svet_dir())
        self.assertTrue(p.endswith("svet"))
        self.assertGreater(len(p), len("/.svet"))


def run(args: List[str]):
    if verbose:
        print(f"Running {args}")
    subprocess.run(args, shell=True)


def runseq(commands: List[str]):
    bash_lines = [
        "#!/bin/bash"
        "set -e",  # fail on first error
    ]

    bash_lines.extend(commands)

    # Ubuntu really needs executable='/bin/bash'.
    # Otherwise the command is executed in /bin/sh, ignoring the hashbang,
    # but SH fails to execute commands like 'source'

    subprocess.call("\n".join(bash_lines), shell=True, executable='/bin/bash')


def quote(arg: str) -> str:
    return json.dumps(arg)


def venv_dir_to_exe(venv_dir: Path) -> Path:
    return venv_dir / "bin" / "python"


def init(venv_dir: Path, version: str):
    if venv_dir.exists():
        raise VenvExistsError("Virtualenv already exists.")

    exe = shutil.which(version)
    if not exe:
        raise CannotFindExecutableError(f"Cannot resolve '{version}' to an executable file.")

    print(f"Creating {venv_dir}")

    result = subprocess.run([exe, "-m", "venv", str(venv_dir)])
    if result.returncode == 0:
        print()
        print("The Python executable:")
        print(str(venv_dir_to_exe(venv_dir)))
    else:
        print("svet failed to create the virtualenv")
        exit(1)


def remove(venv_dir: Path):
    if not "_venv" in venv_dir.name:
        raise ValueError(venv_dir)
    if not venv_dir.exists():
        raise VenvDoesNotExistError
    print(f"Removing {venv_dir}")
    shutil.rmtree(str(venv_dir))


def reinit(venv_dir: Path, version: str):
    if venv_dir.exists():
        remove(venv_dir)
    init(venv_dir=venv_dir, version=version)


def get_bash_ps1():
    """Returns the default BASH prompt."""

    # TL;DR Normal PS1 is actually inaccessible for the child shell of BASH.
    #
    # AG 2021: PS1 is not an environment variable, but a local variable of
    # the shell [2019](https://stackoverflow.com/a/54999265). It seems to be
    # true for both MacOS 10.13 and Ubuntu 18.04.
    #
    # We can see PS1 by typing "echo $PS1" to the prompt, but ...
    #
    # 1) script.sh with `echo $PS1`                    | prints nothing MacOS & Ubuntu
    # 2) module.py with `print(os.environ.get("PS1")   | prints Null MacOS & Ubuntu
    # 3) `bash -i -c "echo $PS1"` from command line    | seems to be OK in Ubuntu
    # 4) `zsh -i -c "echo $PS1"` from command line     | looks like a normal prompt in OSX
    #
    # In Ubuntu (3) seems to be the same as used by terminal by default.
    # Although there are no guarantees it is the same that user sees.
    #
    # For MacOS, the prompt printed by (3) in not the same as seen in terminal app,
    # and boring: "bash-3.2" instead of "host:dir user$".
    #
    # (4) on MacOS seems to return the correct "host:dir user$", but it is in ZSH format.

    # try to return $PS1 environment variable:
    env_var = os.environ.get("PS1")
    if env_var is not None:
        return env_var

    # return None for MacOS
    import platform
    if platform.system() == "Darwin":
        return r"\h:\W \u\$"  # default for MacOS up to Catalina

    # hope for the best in other systems
    return subprocess.check_output(['/bin/bash', '-i', '-c', 'echo $PS1']).decode().rstrip()


class Colors:
    GREEN = r"\e[32m\]"
    MAGENTA = r"\e[35m\]"
    YELLOW = r"\e[33m\]"
    CYAN = r"\e[36m\]"
    BLUE = r"\e[34m\]"
    NOCOLOR = r"\e[0m\]"


def shell(venv_dir: Path, venv_name: str, input: str, input_delay: float):
    if not venv_dir.exists():
        raise VenvDoesNotExistError

    activate_path_quoted = quote(str(venv_dir / "bin" / "activate"))

    old_ps1 = os.environ.get("PS1") or get_bash_ps1()

    if not old_ps1:
        old_ps1 = r"\h:\W \u\$"  # default from MacOS

    new_ps1 = f"\\[{Colors.YELLOW}({venv_name}){Colors.NOCOLOR}:{old_ps1} \\]"

    commands = [f'source {activate_path_quoted}']

    bashrc_file = Path(os.path.expanduser("~/.bashrc"))

    if bashrc_file.exists():
        # Ubuntu
        commands.append(f"exec bash --rcfile <(cat {json.dumps(str(bashrc_file))} && echo 'PS1={json.dumps(new_ps1)}')")
    else:
        # MacOS
        commands.append(f"PS1={json.dumps(new_ps1)} exec bash")

    # we will use [input] for testing: we will send a command to the stdin of
    # the interactive sub-shell and later check whether the command was executed.
    #
    # We will also provide [input_delay] parameter. This allows the check whether
    # the sub-shell was really interactive: did it wait for the input
    #
    # Surprisingly, the sub-shell will immediately close after executing the command.
    # It seems it closes immediately after the subprocess.Popen closes the stdin.
    # So it will not wait for "exit". But it serves the task well

    run_as_bash_script("\n".join(commands), input=input.encode() if input else None,
                       input_delay=input_delay)


def command_run(venv_dir: Path, otherargs):
    vd = str(venv_dir.absolute())
    commands = [
        f'source "{vd}/bin/activate"',
        " ".join(quote(a) for a in otherargs)
    ]

    exit(runseq(commands))


def main_entry_point(args: Optional[List[str]] = None):
    if args is None:
        args = sys.argv[1:]

    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest='command', required=True)

    parser_init = subparsers.add_parser('create', help="create new virtualenv")
    parser_init.add_argument('python', type=str, default="python3", nargs='?')

    subparsers.add_parser('delete', help="delete existing virtualenv")

    parser_reinit = subparsers.add_parser('recreate',
                                          help="delete existing virtualenv and create new")
    parser_reinit.add_argument('python', type=str, default="python3", nargs='?')

    shell_parser = subparsers.add_parser('shell', help="dive into Bash sub-shell using the virtualenv")
    shell_parser.add_argument("--input", type=str, default=None)
    shell_parser.add_argument("--delay", type=float, default=None, help=argparse.SUPPRESS)

    parser_run = subparsers.add_parser('run', help="run a command inside the virtualenv")
    parser_run.add_argument('otherargs', nargs=argparse.REMAINDER)

    subparsers.add_parser('path',
                          help="show the supposed path of the virtualenv for the current directory")

    if not args:
        print(usage_doc())
        parser.print_help()
        exit(2)

    parsed = parser.parse_args(args)

    ###########

    project_dir = Path(".").absolute()
    venv_dir = get_svet_dir() / (project_dir.name + "_venv")

    if verbose:
        print(f"Proj dir: {project_dir}")
        print(f"Venv dir: {venv_dir}")

    ##########

    if parsed.command == "create":
        init(venv_dir, parsed.python)
    elif parsed.command == "recreate":
        reinit(venv_dir, parsed.python)
    elif parsed.command == "delete":
        remove(venv_dir)
    elif parsed.command == "path":
        print(venv_dir)
    elif parsed.command == "run":
        command_run(venv_dir, parsed.otherargs)
    elif parsed.command == "shell":
        shell(venv_dir, project_dir.name, parsed.input, parsed.delay)
    else:
        raise ValueError
