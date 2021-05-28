# SPDX-FileCopyrightText: (c) 2021 Artëm IG <github.com/rtmigo>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path


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


class VenvExistsExit(VienExit):
    def __init__(self, path: Path):
        super().__init__(f'Virtual environment "{path}" already exists.')


class VenvDoesNotExistExit(VienExit):
    def __init__(self, path: Path):
        super().__init__(f'Virtual environment "{path}" does not exist.\n'
                         f'You can create it with "vien create".')


class PyFileNotFoundExit(VienExit):
    def __init__(self, path: Path):
        super().__init__(f"File {path} not found.")


class PyFileArgNotFoundExit(VienExit):
    def __init__(self):
        super().__init__(f"The arguments to the 'call' command must "
                         f"include a .py file.")


class FailedToCreateVenvExit(VienExit):
    def __init__(self, path: Path):
        super().__init__(f"Failed to create virtual environment {path}.")


class FailedToClearVenvExit(VienExit):
    def __init__(self, path: Path):
        super().__init__(f"Failed to clear virtual environment {path}.")


class CannotFindExecutableExit(VienExit):
    def __init__(self, version: str):
        super().__init__(f"Cannot resolve '{version}' to an executable file.")
