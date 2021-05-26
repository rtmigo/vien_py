import os

is_windows = os.name == 'nt'
is_posix = os.name == 'posix'

if not is_windows and not is_posix:
    raise SystemExit(f"System '{os.name}' is not supported.")


class UnexpectedOsError(Exception):
    pass


def need_posix():
    if not is_posix:
        raise UnexpectedOsError


def need_windows():
    if not is_windows:
        raise UnexpectedOsError
