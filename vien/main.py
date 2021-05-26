# SPDX-FileCopyrightText: (c) 2020 Artëm IG <github.com/rtmigo>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import shlex
from pathlib import Path
from typing import *

from vien import is_posix
from vien._common import need_posix, is_windows, need_windows
from vien.arg_parser import Commands, Parsed
from vien.bash_runner import run_as_bash_script
from vien.call_parser import call_pyfile
from vien.colors import Colors
from vien.escaping_cmd import cmd_escape_arg
from vien.exceptions import ChildExit, VenvExistsExit, VenvDoesNotExistExit, \
    PyFileNotFoundExit, PyFileArgNotFoundExit, FailedToCreateVenvExit, \
    FailedToClearVenvExit, CannotFindExecutableExit

verbose = False


def exe_name() -> str:
    return os.path.basename(sys.argv[0])


def get_vien_dir() -> Path:
    path_from_var = os.environ.get("VIENDIR")
    if path_from_var:
        path_from_var = os.path.expandvars(path_from_var)
        path_from_var = os.path.expanduser(path_from_var)
        return Path(path_from_var)
    else:
        # It looks like storing dot files in the home directory
        # is the de facto standard for both worlds.
        #
        # App    | POSIX     | Windows
        # -------|-----------|----------------------
        # VSCode | ~/.vscode | %USERPROFILE%\.vscode
        # AWS:   | ~/.aws    | %USERPROFILE%\.aws
        #
        return Path.home() / ".vien"


def run_bash_sequence(commands: List[str], env: Optional[Dict] = None) -> int:
    need_posix()

    # command || exit /b 666

    lines = [
        # shebang not necessary as we specify executable in subprocess.call
        "set -e",  # fail on first error
    ]

    lines.extend(commands)

    # Ubuntu really needs executable='/bin/bash'.
    # Otherwise the command is executed in /bin/sh, ignoring the hashbang,
    # but SH fails to execute commands like 'source'

    return subprocess.call("\n".join(lines),
                           shell=True,
                           executable='/bin/bash',
                           env=env)


def run_cmdexe_sequence(commands: List[str], env: Optional[Dict] = None) -> int:
    # todo test independently
    # This function does not work "officially" yet.

    need_windows()

    # raise NotImplemented

    # https://stackoverflow.com/questions/734598/how-do-i-make-a-batch-file-terminate-upon-encountering-an-error

    # unlike bash, cmd.exe returns exit code zero even if last command returned
    # non-zero. There is also no evident way to turn on 'set -e' mode, i.e.
    # exit on the first failure.
    #
    # We'll just glue all the commands with &&

    glued = " && ".join(f'( {c} )' for c in commands)

    # print(f"CMD running {glued}")

    return subprocess.call(glued,
                           shell=True,
                           # executable='/bin/bash',
                           env=env)


def venv_dir_to_python_exe(venv_dir: Path) -> Path:
    # this method is being tested indirectly each time the venv is created:
    # vien prints the path to executable after running this function

    if is_posix:
        parent = venv_dir / "bin"
        basenames = "python", "python3"
    else:
        parent = venv_dir / "Scripts"
        basenames = "python.exe", "python3.exe"

    for name in basenames:
        executable = parent / name
        if executable.exists():
            return executable

    raise Exception(f"Cannot find the Python interpreter in {venv_dir}.")


def windows_cmdexe_activate(venv_dir: Path) -> Path:
    # https://docs.python.org/3/library/venv.html
    assert is_windows
    return venv_dir / 'Scripts' / 'activate.bat'


def posix_bash_activate(venv_dir: Path) -> Path:
    # https://docs.python.org/3/library/venv.html
    assert is_posix
    return venv_dir / 'bin' / 'activate'


def arg_to_python_interpreter(argument: Optional[str]) -> str:
    if argument is None:
        return sys.executable
    exe = shutil.which(argument)
    if not exe:
        raise CannotFindExecutableExit(argument)
    return exe


def main_create(venv_dir: Path, interpreter: Optional[str]):
    if venv_dir.exists():
        raise VenvExistsExit("Virtualenv already exists.")

    exe = arg_to_python_interpreter(interpreter)

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

    # todo try to use the same executable that created the environment
    # If we use sys.executable, we may clear the venv in some incompatible way.
    # But we can't just use executable from the venv when clearing it:
    # Windows will fail with [WinError 5] Access is denied: '...python.exe'

    # todo check we are not running the same executable we about to delete
    # python_exe = venv_dir_to_python_exe(venv_dir)
    print(f"Clearing {venv_dir}")

    result = subprocess.run(
        [sys.executable, "-m", "venv", "--clear", str(venv_dir)],
        capture_output=True, encoding=sys.stdout.encoding)
    if result.returncode != 0:
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        raise FailedToClearVenvExit(venv_dir)
    print(f"Deleting {venv_dir}")
    shutil.rmtree(str(venv_dir))


def main_recreate(venv_dir: Path, interpreter: Optional[str]):
    if venv_dir.exists():
        main_delete(venv_dir)
    main_create(venv_dir=venv_dir, interpreter=interpreter)


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


def main_shell(dirs: Dirs, input: Optional[str], input_delay: Optional[float]):
    dirs.venv_must_exist()

    activate_path_quoted = shlex.quote(
        str(dirs.venv_dir / "bin" / "activate"))

    old_ps1 = os.environ.get("PS1") or guess_bash_ps1()

    if not old_ps1:
        old_ps1 = r"\h:\W \u\$"  # default from MacOS

    color_start = Colors.YELLOW
    color_end = Colors.NOCOLOR

    venv_name = dirs.project_dir.name
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
                            input_delay=input_delay,
                            env=child_env(dirs.project_dir))

    # the vien will return the same exit code as the shell returned
    raise ChildExit(cp.returncode)


def bash_args_to_str(args: List[str]) -> str:
    return ' '.join(shlex.quote(arg) for arg in args)


def cmdexe_args_to_str(args: List[str]) -> str:
    return ' '.join(cmd_escape_arg(arg) for arg in args)


def main_run(dirs: Dirs, command: List[str]):
    dirs.venv_must_exist()

    sequence: List[str] = list()

    if is_posix:
        activate_file = posix_bash_activate(dirs.venv_dir)
        sequence.append(f'source {shlex.quote(str(activate_file))}')
        sequence.append(bash_args_to_str(command))
        run_func = run_bash_sequence
    elif is_windows:
        activate_file = windows_cmdexe_activate(dirs.venv_dir)
        sequence.append(f'CALL {activate_file}"')
        sequence.append(cmdexe_args_to_str(command))
        run_func = run_cmdexe_sequence
    else:
        raise AssertionError("Unexpected OS")
    #    activate_file = (dirs.venv_dir / 'bin' / 'activate').absolute()
    if not activate_file.exists():
        raise FileNotFoundError(activate_file)

    exit_code = run_func(sequence, env=child_env(dirs.project_dir))
    raise ChildExit(exit_code)


class Dirs:
    def __init__(self, project_dir: Union[str, Path] = '.'):
        self.project_dir = Path(project_dir).absolute()
        self.venv_dir = get_vien_dir() / (self.project_dir.name + "_venv")
        if verbose:
            print(f"Proj dir: {self.project_dir}")
            print(f"Venv dir: {self.venv_dir}")

    def venv_must_exist(self) -> Dirs:
        if not self.venv_dir.exists():
            raise VenvDoesNotExistExit(self.venv_dir)
        return self


def _insert_into_pythonpath(insert_me: str) -> str:
    # https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH
    # "The format is the same as the shell’s PATH: one or more directory
    # pathnames separated by os.pathsep (e.g. colons on Unix or semicolons
    # on Windows)"
    ####
    # $PYTHONPATH and sys.path are not the same.
    # - sys.path contains directories used by the current interpreter
    #   (the one that runs vien)
    # - $PYTHONPATH is the variable to be used by all interpreters
    #
    # For example, if we run vien on Python 3.7 and trying to use venv with
    # Python 3.9, we should not provide out own sys.path (3.7) to the child
    # interpreter (3.9).

    parts = [p.strip() for p in
             os.environ.get("PYTHONPATH", '').split(os.pathsep)]
    parts = [p for p in parts if p]

    if insert_me not in parts:
        parts.insert(0, insert_me)
    return os.pathsep.join(parts)


def child_env(proj_path: Path) -> Optional[Dict]:
    env: Optional[Dict]
    if proj_path != Path.cwd():
        return {
            **os.environ,
            'PYTHONPATH': _insert_into_pythonpath(str(proj_path))
        }
    else:
        return None


def main_call(venv_dir: Path,
              proj_path: Path,
              other_args: List[str]):
    python_exe = venv_dir_to_python_exe(venv_dir)
    # print("EXE",python_exe)
    assert len(other_args) > 0
    args = [str(python_exe)] + other_args

    cp = subprocess.run(args, env=child_env(proj_path))

    raise ChildExit(cp.returncode)


def normalize_path(reference: Path, path: Path) -> Path:
    # todo test
    if path.is_absolute():
        return path
    return Path(os.path.normpath(reference / path))


def get_project_dir(parsed: Parsed) -> Path:
    if parsed.project_dir_arg is not None:
        if parsed.command == Commands.call:
            # for the 'call' the reference dir is the parent or .py file
            pyfile = call_pyfile(parsed.args)
            if pyfile is None:
                raise PyFileArgNotFoundExit
            reference_dir = Path(pyfile).parent.absolute()
        else:
            # for other commands the reference dir is cwd
            reference_dir = Path(".").absolute()
        project_dir = normalize_path(reference_dir,
                                     Path(parsed.project_dir_arg))
    else:
        # when the --project-dir is not specified, the project dir is cwd
        assert parsed.project_dir_arg is None
        project_dir = Path('.')
    project_dir = project_dir.absolute()
    return project_dir


def main_entry_point(args: Optional[List[str]] = None):
    parsed = Parsed(args)

    # todo replace private _ns attrs with public properties

    dirs = Dirs(project_dir=get_project_dir(parsed))

    if parsed.command == Commands.create:
        main_create(dirs.venv_dir, parsed.python_executable)
    elif parsed.command == Commands.recreate:
        main_recreate(dirs.venv_dir,
                      parsed.python_executable)  # todo .existing()?
    elif parsed.command == Commands.delete:  # todo move 'existing' check from func?
        main_delete(dirs.venv_dir)
    elif parsed.command == Commands.path:
        print(dirs.venv_dir)  # does not need to be existing
    elif parsed.command == Commands.run:
        # todo allow running commands from strings
        main_run(dirs.venv_must_exist(), parsed.run_args)
    elif parsed.command == Commands.call:
        # todo move in func
        dirs.venv_must_exist()
        pyfile_arg = call_pyfile(parsed.args)
        assert pyfile_arg is not None
        if not os.path.exists(pyfile_arg):
            raise PyFileNotFoundExit(Path(pyfile_arg))
        main_call(venv_dir=dirs.venv_dir,
                  proj_path=dirs.project_dir,
                  other_args=parsed.args_to_python)

    elif parsed.command == Commands.shell:
        main_shell(dirs, parsed.shell_input, parsed.shell_delay)
    else:
        raise ValueError
