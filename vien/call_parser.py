from typing import Iterable, List, Optional, Tuple

from vien.exceptions import PyFileArgNotFoundExit


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
    __slots__ = ['args', 'file', 'file_idx']

    def __init__(self, args: List[str]):

        self.args = args

        call_found = False
        file_found = False
        for idx, arg in enumerate(args):
            if not call_found:
                if arg == "call":
                    call_found = True
                continue

            if arg.lower().endswith(".py"):
                self.file = arg
                self.file_idx = idx
                file_found = True
                break

        if not file_found:
            raise PyFileArgNotFoundExit

    @property
    def before_filename(self) -> Optional[str]:
        if self.file_idx <= 0:
            return None
        val = self.args[self.file_idx - 1]
        if val == "call":
            return None
        return val

# def call_pyfile(args: List[str]) -> Optional[str]:
#     # todo remove?
#     for arg in items_after(args, "call"):
#         if arg.lower().endswith(".py"):
#             return arg
#     return None
