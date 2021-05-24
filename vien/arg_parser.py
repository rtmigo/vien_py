import argparse
import sys
from enum import Enum
from typing import List, Optional

import vien
from vien.call_parser import items_after


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


def remove_leading_p(args: List[str]) -> List[str]:
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


class Parsed:
    def __init__(self, args: Optional[List[str]]):
        super().__init__()

        parser = argparse.ArgumentParser()

        parser.add_argument("--project-dir", "-p", default=None, type=str)

        subparsers = parser.add_subparsers(dest='command', required=True)

        parser_init = subparsers.add_parser(Commands.create.name,
                                            help="create new virtualenv")
        parser_init.add_argument('python', type=str, default="python3",
                                 nargs='?')

        subparsers.add_parser(Commands.delete.name,
                              help="delete existing virtualenv")

        parser_reinit = subparsers.add_parser(
            Commands.recreate.name,
            help="delete existing virtualenv and create new")
        parser_reinit.add_argument('python', type=str, default="python3",
                                   nargs='?')

        shell_parser = subparsers.add_parser(
            Commands.shell.name,
            help="dive into Bash sub-shell using the virtualenv")
        shell_parser.add_argument("--input", type=str, default=None)
        shell_parser.add_argument("--delay", type=float, default=None,
                                  help=argparse.SUPPRESS)

        parser_run = subparsers.add_parser(
            Commands.run.name,
            help="run a command inside the virtualenv")
        parser_run.add_argument('otherargs', nargs=argparse.REMAINDER)

        parser_call = subparsers.add_parser(
            Commands.call.name,
            help="run a script inside the virtualenv")
        # todo Remove it later. [call -p] is outdated since 2021-05
        parser_call.add_argument("--project-dir", "-p", default=None, type=str,
                                 dest="outdated_call_project_dir",
                                 help=argparse.SUPPRESS)
        # this arg is for help only. Actually it's buggy (at least in 3.7),
        # so we will never use its result, and get those args other way
        parser_call.add_argument('args_to_python', nargs=argparse.REMAINDER)

        subparsers.add_parser(
            Commands.path.name,
            help="show the supposed path of the virtualenv "
                 "for the current directory")

        if args is None:
            args = sys.argv[1:]

        if not args:
            print(usage_doc())
            parser.print_help()
            exit(2)

        self.args = args

        # it seems, nargs.REMAINDER is buggy in 2021:
        # https://bugs.python.org/issue17050
        #
        # For example, when the first REMAINDER argument is an option
        # such as "-d", argparse shows error instead of just remembering "-d"
        #
        # But "-d" actually can be the first REMAINDER arg after the CALL
        # command.
        #
        # That's why we parse args twice. First time with `parse_known_args` -
        # to get the command name. And then, if it's not CALL - we parse
        # again with a stricter parse_args.

        self._ns: argparse.Namespace
        unknown: List[str]

        self._ns, unknown = parser.parse_known_args(self.args)
        if self.command == Commands.call:
            self.args_to_python = list(items_after(args, 'call'))

            # if some of the unknown args are NOT after the 'call',
            # then we're failed to interpret the command. Parsing
            # it stricter
            bad_unrecognized = [unk for unk in unknown if
                                unk not in self.args_to_python]
            if bad_unrecognized:
                parser.error(f"unrecognized arguments: {bad_unrecognized}")
                raise AssertionError("Not expected to run this line")

            # todo Remove later. [call -p] is outdated since 2021-05
            self.args_to_python = remove_leading_p(self.args_to_python)
        else:
            # if some args were not recognized, parsing everything stricter
            if unknown:
                self._ns = parser.parse_args(self.args)

    @property
    def command(self) -> Commands:
        return Commands(self._ns.command)

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
    def python_executable(self) -> str:
        if self.command not in (Commands.create, Commands.recreate):
            raise RuntimeError
        assert self._ns.python is not None
        return self._ns.python
