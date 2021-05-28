# SPDX-FileCopyrightText: (c) 2021 Artëm IG <github.com/rtmigo>
# SPDX-License-Identifier: BSD-3-Clause

import argparse
import os
import sys
from enum import Enum
from typing import List, Optional, Iterable

from vien._common import is_windows

from vien import is_posix

import vien
# from vien.call_parser import items_after
from vien._parsed_call import ParsedCall


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


def _iter_after(items: Iterable[str], x: str) -> Iterable[str]:
    found = False
    for arg in items:
        if found:
            yield arg
        elif arg == x:
            found = True
    if not found:
        raise LookupError


def _remove_leading_p(args: List[str]) -> List[str]:
    # fixing a problem that is outdated since 2021-05
    if len(args) < 2:
        return args
    if args[0] == "-p" or args[0] == "--project-dir":
        args = args[2:]
    return args


class Commands(Enum):
    create = "create"
    delete = "delete"
    recreate = "recreate"
    shell = "shell"
    run = "run"
    call = "call"
    path = "path"


class TempColumns:
    def __init__(self, width: int):
        self.width = width
        self._old_value: Optional[str] = None

    def __enter__(self):
        self._old_value = os.environ.get('COLUMNS')

        new_value_int = self.width

        try:
            old_value_int = int(self._old_value)
            new_value_int = min(old_value_int, new_value_int)
        except (ValueError, TypeError):
            pass

        os.environ['COLUMNS'] = str(new_value_int)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._old_value is not None:
            os.environ['COLUMNS'] = self._old_value


class ParsedArgs:
    PARAM_WINDOWS_ALL_ARGS = "--vien-secret-windows-all-args"

    def __init__(self, args: Optional[List[str]]):
        with TempColumns(80):

            self._call: Optional[ParsedCall] = None

            if args is None:
                args = sys.argv[1:]

            # secret parameter PARAM_WINDOWS_ALL_ARGS allows to run commands that
            # are not yet fully supported on Windows.
            enable_windows_all_args = self.PARAM_WINDOWS_ALL_ARGS in args
            if enable_windows_all_args:
                # for more transparent testing, I don't want this param
                # to ever affect posix behavior
                assert is_windows

            parser = argparse.ArgumentParser()

            parser.add_argument("--project-dir", "-p", default=None, type=str,
                                help="the Python project directory "
                                     "(default: current working directory). "
                                     "Implicitly determines which virtual "
                                     "environment should be used for the "
                                     "command")

            # the following parameter is added only to avoid parsing errors.
            # Actually we use its value from `args` before running
            # ArgumentParser
            parser.add_argument(self.PARAM_WINDOWS_ALL_ARGS,
                                action='store_true',
                                help=argparse.SUPPRESS)

            subparsers = parser.add_subparsers(dest='command', required=True)

            parser_init = subparsers.add_parser(
                Commands.create.name,
                help="create new virtual environment")
            parser_init.add_argument('python', type=str, default=None,
                                     nargs='?')

            subparsers.add_parser(Commands.delete.name,
                                  help="delete existing environment")

            parser_reinit = subparsers.add_parser(
                Commands.recreate.name,
                help="delete existing environment and create new")
            parser_reinit.add_argument('python', type=str, default=None,
                                       nargs='?')

            if is_posix or enable_windows_all_args:
                shell_parser = subparsers.add_parser(
                    Commands.shell.name,
                    help="dive into Bash sub-shell with the environment")
                shell_parser.add_argument("--input", type=str, default=None)
                shell_parser.add_argument("--delay", type=float, default=None,
                                          help=argparse.SUPPRESS)

            if is_posix or enable_windows_all_args:
                parser_run = subparsers.add_parser(
                    Commands.run.name,
                    help="run a shell command in the environment")
                parser_run.add_argument('otherargs', nargs=argparse.REMAINDER)

            parser_call = subparsers.add_parser(
                Commands.call.name,
                help="run a .py file in the environment")
            # todo Remove it later. [call -p] is outdated since 2021-05
            parser_call.add_argument("--project-dir", "-p", default=None,
                                     type=str,
                                     dest="outdated_call_project_dir",
                                     help=argparse.SUPPRESS)
            # this arg is for help only. Actually it's buggy (at least in 3.7),
            # so we will never use its result, and get those args other way
            parser_call.add_argument('args_to_python', nargs=argparse.REMAINDER)

            subparsers.add_parser(
                Commands.path.name,
                help="show the path of the environment "
                     "for the project")

            if not args:
                print(usage_doc())
                parser.print_help()
                exit(2)

            self.args = args

            # it seems, nargs.REMAINDER is buggy in 2021:
            # https://bugs.python.org/issue17050
            #
            # For example, when the first REMAINDER argument is an option
            # such as "-d", argparse shows error instead of just
            # remembering "-d"
            #
            # But "-d" actually can be the first REMAINDER arg after the CALL
            # command.
            #
            # That's why we parse args twice. First time with
            # `parse_known_args` - to get the command name. And then, if it's
            # not CALL - we parse again with a stricter parse_args.

            self._ns: argparse.Namespace
            unknown: List[str]

            self._ns, unknown = parser.parse_known_args(self.args)
            if self._ns.command == 'call':
                self.args_to_python = list(_iter_after(args, 'call'))

                # if some of the unknown args are NOT after the 'call',
                # then we're failed to interpret the command
                bad_unrecognized = [unk for unk in unknown if
                                    unk not in self.args_to_python]
                if bad_unrecognized:
                    parser.error(f"unrecognized arguments: {bad_unrecognized}")
                    raise AssertionError("Not expected to run this line")

                # todo Remove later. [call -p] is outdated since 2021-05
                self.args_to_python = _remove_leading_p(self.args_to_python)
                self._call = ParsedCall(args)
            else:
                # if some args were not recognized, parsing everything stricter
                if unknown:
                    self._ns = parser.parse_args(self.args)

            self.command = Commands(self._ns.command)

    # @property
    # def command(self) -> Commands:
    #     return Commands(self._ns.command)

    @property
    def call(self) -> ParsedCall:
        if self.command != Commands.call:
            raise RuntimeError("The current command is not 'call'")
        assert self._call is not None
        return self._call

    @property
    def project_dir_arg(self) -> Optional[str]:
        """Returns either outdated [call -p ARG] or normal [vien -p ARG]
        value."""
        project_dir_after_call = self._ns.__dict__ \
            .get('outdated_call_project_dir')
        if project_dir_after_call is not None:
            print("'vien call -p proj/dir file.py' syntax is outdated. "
                  "Use 'vien -p proj/dir call file.py'.")
            return project_dir_after_call
        return self._ns.project_dir

    @property
    def python_executable(self) -> Optional[str]:
        if self.command not in (Commands.create, Commands.recreate):
            raise RuntimeError
        # assert self._ns.python is not None
        return self._ns.python

    @property
    def shell_input(self) -> Optional[str]:
        if self.command != Commands.shell:
            raise RuntimeError
        return self._ns.input

    @property
    def shell_delay(self) -> Optional[float]:
        if self.command != Commands.shell:
            raise RuntimeError
        return self._ns.delay

    @property
    def run_args(self) -> List[str]:
        if self.command != Commands.run:
            raise RuntimeError
        return self._ns.otherargs
