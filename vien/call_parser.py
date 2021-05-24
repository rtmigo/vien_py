from typing import Iterable, List, Optional, Tuple


def items_after(items: Iterable[str], x: str) -> Iterable[str]:
    found = False
    for arg in items:
        if found:
            yield arg
        elif arg == x:
            found = True
    if not found:
        raise LookupError


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


def call_pyfile(args: List[str]) -> Optional[str]:
    for arg in items_after(args, "call"):
        if arg.lower().endswith(".py"):
            return arg
    return None
