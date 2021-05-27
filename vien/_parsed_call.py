# SPDX-FileCopyrightText: (c) 2021 Artëm IG <github.com/rtmigo>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Iterable, List, Optional, Tuple

from vien._exceptions import PyFileArgNotFoundExit


def list_left_partition(items: Iterable[str], split: str) \
        -> Tuple[List[str], List[str]]:
    # todo test
    left = list()
    right = list()

    found = False
    for arg in items:
        if not found:
            if arg == split:
                found = True
                continue
            left.append(arg)
        else:
            right.append(arg)

    return left, right


class ParsedCall:
    __slots__ = ['args', 'filename', 'filename_idx']

    def __init__(self, args: List[str]):

        self.args = args

        call_found = False
        file_found = False
        for idx, arg in enumerate(args):
            if not call_found:
                if arg == "call":
                    call_found = True
                continue

            if len(arg) > 3 and arg[-3:].lower() == ".py":
                self.filename = arg
                self.filename_idx = idx
                file_found = True
                break

        if not file_found:
            raise PyFileArgNotFoundExit

    @property
    def before_filename(self) -> Optional[str]:
        """Returns the argument before the filename, but after the 'call'.
        For command 'vien call -m file.py' it is '-m'.
        For command 'vien call file.py' it is None.
        """
        if self.filename_idx <= 0:
            return None
        val = self.args[self.filename_idx - 1]
        if val == "call":
            return None
        return val
