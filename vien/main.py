# SPDX-FileCopyrightText: (c) 2020 Artëm IG <github.com/rtmigo>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import *

import vien
from vien.bash_runner import run_as_bash_script
from vien.colors import Colors

verbose = False


def exe_name() -> str:
    return os.path.basename(sys.argv[0])


class VienExit(SystemExit):
    """Base class for all the expected exceptions,
    that show the error message and stop the program."""

    def __init__(self, arg):
        super().__init__(arg)


class ChildExit(VienExit):
    """When a child process finished, and vien must exit too with
    the same code"""

    def __init__(self, exit_code: int):
        super().__init__(exit_code)


class VenvExistsExit(VienExit):  # todo does it return error code?
    pass


class VenvDoesNotExistExit(VienExit):
    def __init__(self, path: Path):
        super().__init__(f'Virtual environment "{path}" does not exist.\n'
                         f'You can create it with "{exe_name()} create".')


class PyFileNotFoundExit(VienExit):
    def __init__(self, path: Path):
        super().__init__(f"File {path} not found.")


class FailedToCreateVenvExit(VienExit):
    def __init__(self, path: Path):
        super().__init__(f"Failed to create virtualenv {path}.")


class FailedToClearVenvExit(VienExit):
    def __init__(self, path: Path):
        super().__init__(f"Failed to clear virtualenv {path}.")


class CannotFindExecutableExit(VienExit):
    def __init__(self, version: str):
        super().__init__(f"Cannot resolve '{version}' to an executable file.")


def version_message() -> str:
    return "\n".join([
        f"VIEN: Python Virtual Environments Tool {vien.__version__}",
        vien.__copyright__
    ])


def usage_doc():
    text = f"""{version_message()}

See a detailed intro at
https://github.com/rtmigo/vien_py#readme

"""

    doc = text.strip()
    above_first_line = ("-" * len(doc.splitlines()[0]))
    return f"{above_first_line}\n{doc}\n"


def get_vien_dir() -> Path:
    s = os.environ.get("VIENDIR")
    if s:
        return Path(os.path.expanduser(os.path.expandvars(s)))
    else:
        return Path(os.path.expandvars("$HOME")) / ".vien"


def run_bash_sequence(commands: List[str]) -> int:
    bash_lines = [
        "#!/bin/bash"
        "set -e",  # fail on first error
    ]

    bash_lines.extend(commands)

    # Ubuntu really needs executable='/bin/bash'.
    # Otherwise the command is executed in /bin/sh, ignoring the hashbang,
    # but SH fails to execute commands like 'source'

    return subprocess.call("\n".join(bash_lines),
                           shell=True,
                           executable='/bin/bash')


def quote(arg: str) -> str:
    return json.dumps(arg)


def venv_dir_to_python_exe(venv_dir: Path) -> Path:
    for sub in ("bin/python", "bin/python3"):
        p = venv_dir / sub
        if p.exists():
            return p
    raise Exception(f"Cannot find the Python interpreter in {venv_dir}.")


def get_python_interpreter(argument: str) -> str:
    exe = shutil.which(argument)
    if not exe:
        raise CannotFindExecutableExit(argument)
    return exe


def main_create(venv_dir: Path, version: str):
    if venv_dir.exists():
        raise VenvExistsExit("Virtualenv already exists.")

    exe = get_python_interpreter(version)

    print(f"Creating {venv_dir}")

    result = subprocess.run([exe, "-m", "venv", str(venv_dir)])
    if result.returncode == 0:
        print()
        print("The Python executable:")
        print(str(venv_dir_to_python_exe(venv_dir)))
    else:
        raise FailedToCreateVenvExit(venv_dir)


def main_delete(venv_dir: Path):
    if "_venv" not in venv_dir.name:
        raise ValueError(venv_dir)
    if not venv_dir.exists():
        raise VenvDoesNotExistExit(venv_dir)
    python_exe = venv_dir_to_python_exe(venv_dir)
    print(f"Clearing {venv_dir}")

    result = subprocess.run([python_exe, "-m", "venv", str(venv_dir)])
    if result.returncode != 0:
        raise FailedToClearVenvExit(venv_dir)
    print(f"Deleting {venv_dir}")
    shutil.rmtree(str(venv_dir))


def main_recreate(venv_dir: Path, version: str):
    if venv_dir.exists():
        main_delete(venv_dir)
    main_create(venv_dir=venv_dir, version=version)


def guess_bash_ps1():
    """Returns the default BASH prompt."""

    # TL;DR PS1 is often inaccessible for child processes of BASH. It means,
    # for scripts too.
    #
    # AG 2021: PS1 is not an environment variable, but a local variable of
    # the shell [2019](https://stackoverflow.com/a/54999265). It seems to be
    # true for both MacOS 10.13 and Ubuntu 18.04.
    #
    # We can see PS1 by typing "echo $PS1" to the prompt, but ...
    #
    # 1) script.sh with `echo $PS1`        | prints nothing MacOS & Ubuntu
    #
    # 2) module.py with                    | prints Null MacOS & Ubuntu
    #    `print(os.environ.get("PS1")      |
    #
    # 3) `bash -i -c "echo $PS1"`          | seems to be OK in Ubuntu
    #     from command line                |
    #
    # 4) `zsh -i -c "echo $PS1"`           | looks like a normal prompt in OSX
    #     from command line                |
    #
    # In Ubuntu (3) returns the same prompt that in used by terminal by default.
    # Although if the user customized their PS1, no guarantees, that (3) will
    # return the updated value.
    #
    # For MacOS, the prompt printed by (3) in not the same as seen in terminal
    # app. It returns boring "bash-3.2" instead of expected "host:dir user$".
    #
    # (4) on MacOS seems to return the correct "host:dir user$", but it is in
    # ZSH format.

    # try to return $PS1 environment variable:
    env_var = os.environ.get("PS1")
    if env_var is not None:
        return env_var

    # for MacOS return predefined constant PS1
    import platform
    if platform.system() == "Darwin":
        return r"\h:\W \u\$"  # default for MacOS up to Catalina

    # hope for the best in other systems
    return subprocess.check_output(
        ['/bin/bash', '-i', '-c', 'echo $PS1']).decode().rstrip()


def main_shell(venv_dir: Path, venv_name: str, input: str, input_delay: float):
    if not venv_dir.exists():
        raise VenvDoesNotExistExit(venv_dir)

    activate_path_quoted = quote(str(venv_dir / "bin" / "activate"))

    old_ps1 = os.environ.get("PS1") or guess_bash_ps1()

    if not old_ps1:
        old_ps1 = r"\h:\W \u\$"  # default from MacOS

    color_start = Colors.YELLOW
    color_end = Colors.NOCOLOR

    new_ps1 = f"{color_start}({venv_name}){color_end}:{old_ps1} "

    commands = [f'source {activate_path_quoted}']

    bashrc_file = Path(os.path.expanduser("~/.bashrc"))

    if bashrc_file.exists():
        # Ubuntu
        commands.append(
            f"exec bash --rcfile <(cat {json.dumps(str(bashrc_file))} "
            f"&& echo 'PS1={json.dumps(new_ps1)}')")
    else:
        # MacOS
        commands.append(f"PS1={json.dumps(new_ps1)} exec bash")

    # we will use [input] for testing: we will send a command to the stdin of
    # the interactive sub-shell and later check whether the command was
    # executed.
    #
    # We will also provide [input_delay] parameter. This allows the check
    # whether
    # the sub-shell was really interactive: did it wait for the input
    #
    # Surprisingly, the sub-shell will immediately close after executing the
    # command.  It seems it closes immediately after the subprocess.Popen
    # closes the stdin. So it will not wait for "exit". But it serves the
    # task well

    cp = run_as_bash_script("\n".join(commands),
                            input=input.encode() if input else None,
                            input_delay=input_delay)

    # the vien will return the same exit code as the shell returned
    raise ChildExit(cp.returncode)


def _run(venv_dir: Path, other_args: List[str], prepend_py_path: str = None):
    activate_file = (venv_dir / 'bin' / 'activate').absolute()
    if not activate_file.exists():
        raise FileNotFoundError(activate_file)

    commands: List[str] = list()
    commands.append(f'source "{activate_file}"')
    if prepend_py_path:
        commands.append(f'export PYTHONPATH="{prepend_py_path}:$PYTHONPATH"')
    commands.append(" ".join(quote(a) for a in other_args))

    exit_code = run_bash_sequence(commands)
    raise ChildExit(exit_code)


def main_run(venv_dir: Path, other_args: List[str]):
    _run(venv_dir=venv_dir, other_args=other_args)


class Dirs:
    def __init__(self, project_dir: Union[str, Path] = '.'):
        self.project_dir = Path(project_dir).absolute()
        self.venv_dir = get_vien_dir() / (self.project_dir.name + "_venv")
        if verbose:
            print(f"Proj dir: {self.project_dir}")
            print(f"Venv dir: {self.venv_dir}")

    def existing(self) -> Dirs:
        if not self.venv_dir.exists():
            raise VenvDoesNotExistExit(self.venv_dir)
        return self


def _insert_into_pythonpath(insert_me: str) -> str:
    # https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH
    # "The format is the same as the shell’s PATH: one or more directory
    # pathnames separated by os.pathsep (e.g. colons on Unix or semicolons
    # on Windows)"
    return os.pathsep.join([insert_me] + sys.path)


def main_call(py_file: str, proj_rel_path: Optional[str],
              other_args: List[str]):
    file = Path(py_file)
    if not file.exists():
        raise PyFileNotFoundExit(file)

    assert isinstance(other_args, list)

    if proj_rel_path is not None:
        proj_path = Path(os.path.normpath(file.parent / proj_rel_path))
    else:
        proj_path = Path('.')

    dirs = Dirs(proj_path).existing()

    # todo allow python options (before file name)

    python_exe = venv_dir_to_python_exe(dirs.venv_dir)
    args = [str(python_exe), str(file)] + other_args

    env: Optional[Dict]
    if proj_rel_path:
        env = {
            **os.environ,
            'PYTHONPATH': _insert_into_pythonpath(str(proj_path))
        }
    else:
        env = None

    cp = subprocess.run(args, env=env)

    raise ChildExit(cp.returncode)


def main_entry_point(args: Optional[List[str]] = None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest='command', required=True)

    parser_init = subparsers.add_parser('create', help="create new virtualenv")
    parser_init.add_argument('python', type=str, default="python3", nargs='?')

    subparsers.add_parser('delete', help="delete existing virtualenv")

    parser_reinit = subparsers.add_parser(
        'recreate',
        help="delete existing virtualenv and create new")
    parser_reinit.add_argument('python', type=str, default="python3", nargs='?')

    shell_parser = subparsers.add_parser(
        'shell',
        help="dive into Bash sub-shell using the virtualenv")
    shell_parser.add_argument("--input", type=str, default=None)
    shell_parser.add_argument("--delay", type=float, default=None,
                              help=argparse.SUPPRESS)

    parser_run = subparsers.add_parser(
        'run',
        help="run a command inside the virtualenv")
    parser_run.add_argument('otherargs', nargs=argparse.REMAINDER)

    parser_run = subparsers.add_parser(
        'call',
        help="run a script inside the virtualenv")
    parser_run.add_argument("--project-dir", "-p", default=None, type=str)
    parser_run.add_argument('file_py', type=str)
    parser_run.add_argument('otherargs', nargs=argparse.REMAINDER)

    subparsers.add_parser(
        'path',
        help="show the supposed path of the virtualenv "
             "for the current directory")

    if not args:
        print(usage_doc())
        parser.print_help()
        exit(2)

    parsed = parser.parse_args(args)

    if parsed.command == "create":
        main_create(Dirs().venv_dir, parsed.python)
    elif parsed.command == "recreate":
        main_recreate(Dirs().venv_dir, parsed.python)  # todo .existing()?
    elif parsed.command == "delete":  # todo move 'existing' check from func?
        main_delete(Dirs().venv_dir)
    elif parsed.command == "path":
        print(Dirs().venv_dir)  # does not need to be existing
    elif parsed.command == "run":
        main_run(Dirs().existing().venv_dir, parsed.otherargs)
    elif parsed.command == "call":
        main_call(py_file=parsed.file_py,
                  proj_rel_path=parsed.project_dir,
                  other_args=parsed.otherargs)

    elif parsed.command == "shell":
        dirs = Dirs()  # todo move 'existing' check from func?
        main_shell(dirs.venv_dir,
                   dirs.project_dir.name,
                   parsed.input,
                   parsed.delay)
    else:
        raise ValueError
