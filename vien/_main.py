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
from vien._parsed_args import Commands, ParsedArgs
from vien._bash_runner import run_as_bash_script
from vien._call_funcs import relative_fn_to_module_name, relative_inner_path
from vien._parsed_call import ParsedCall, list_left_partition
from vien._colors import Colors
from vien._cmdexe_escape_args import cmd_escape_arg
from vien._exceptions import ChildExit, VenvExistsExit, VenvDoesNotExistExit, \
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
        raise VenvExistsExit(venv_dir)

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
    #
    ####
    #
    # $PYTHONPATH and sys.path are not the same.
    # - $PYTHONPATH is the variable to be used by all Python interpreters
    #   in the current shell environment
    # - sys.path is values for the current interpreter
    #
    # Passing values from own sys.path to other interpreter would be a mistake.
    # The current interpreter may be Python 3.7, and the other interpreter is
    # Python 3.9. Our sys.path leads to 3.7 system libraries, that are
    # unnecessary and even cause errors if added to $PYTHONPATH of 3.9.
    #
    ######
    # keeping it simple: not parsing the old string, just adding a prefix

    old = os.environ.get("PYTHONPATH", '')
    return f'{insert_me}{os.pathsep}{old}'


def child_env(proj_path: Path) -> Optional[Dict]:
    env: Optional[Dict]
    if proj_path != Path.cwd():
        return {
            **os.environ,
            'PYTHONPATH': _insert_into_pythonpath(str(proj_path))
        }
    else:
        return None


def replace_arg(args: List[str], old: str, new: List[str]) -> List[str]:
    """Replaces first occurrence of `old` with a list of `new` items (zero or
    more items). Raises exception if `old` not found.
    """

    # todo remove?
    result = list()
    replaced = False
    for arg in args:
        if not replaced and arg == old:
            result.extend(new)
            replaced = True
        else:
            result.append(arg)

    assert replaced
    return result


def main_call(parsed: ParsedArgs, dirs: Dirs):
    dirs.venv_must_exist()

    #parsed_call = ParsedCall(parsed.args)
    #assert parsed_call.file is not None

    assert parsed.call is not None

    if not os.path.exists(parsed.call.filename):
        raise PyFileNotFoundExit(Path(parsed.call.filename))

    if parsed.call.before_filename == "-m":
        # todo unit test
        # /abc/project/package/module.py -> package/module.py
        relative = relative_inner_path(parsed.call.filename, dirs.project_dir)
        # package/module.py -> package.module
        module_name = relative_fn_to_module_name(relative)
        # replacing the filename in args with the module name.
        # It is already prefixed with -m
        args = parsed.call.args.copy()
        args[parsed.call.filename_idx] = module_name
        # args to python are those after 'call' word
        _, args_to_python = list_left_partition(args, 'call')
        assert '-m' in args_to_python
        assert module_name in args_to_python
    else:
        args_to_python = parsed.args_to_python

    python_exe = venv_dir_to_python_exe(dirs.venv_dir)

    assert len(args_to_python) > 0
    args = [str(python_exe)] + args_to_python

    cp = subprocess.run(args, env=child_env(dirs.project_dir))

    raise ChildExit(cp.returncode)


def normalize_path(reference: Path, path: Path) -> Path:
    # todo test
    if path.is_absolute():
        return path
    return Path(os.path.normpath(reference / path))


def get_project_dir(parsed: ParsedArgs) -> Path:
    if parsed.project_dir_arg is not None:
        if parsed.command == Commands.call:
            # for the 'call' the reference dir is the parent or .py file
            assert parsed.call is not None
            if parsed.call.filename is None:
                raise PyFileArgNotFoundExit
            reference_dir = Path(parsed.call.filename).parent.absolute()
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
    parsed = ParsedArgs(args)

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

        main_call(parsed, dirs)

    elif parsed.command == Commands.shell:
        main_shell(dirs, parsed.shell_input, parsed.shell_delay)
    else:
        raise ValueError
